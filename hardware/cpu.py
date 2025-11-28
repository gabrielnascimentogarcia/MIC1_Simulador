# hardware/cpu.py
from hardware.registers import Register
from hardware.memory import MainMemory, DirectMappingCache
from hardware.alu import ALU
from software.microcode import CONTROL_STORE, decode_microinstruction, OPCODE_MAP

class CPU:
    def __init__(self):
        # 1. Componentes Físicos
        self.ram = MainMemory()
        self.cache = DirectMappingCache(self.ram)
        self.alu = ALU()
        
        # 2. Registradores (Mapeamento conforme diagrama padrão)
        self.regs = {
            0: Register("None"), 
            1: Register("PC"),
            2: Register("IR"),
            3: Register("SP"),
            4: Register("AC"),
            5: Register("MAR"),
            6: Register("MBR"),
            # Registradores Temporários e de Uso Geral
            7: Register("TIR"),
            8: Register("0", 0),
            9: Register("+1", 1),
            10: Register("-1", -1),
            11: Register("AMASK", 0x0FFF),
            12: Register("SMASK", 0x00FF),
            13: Register("A"),
            14: Register("B"),
            15: Register("C") 
        }
        
        # Registradores Internos
        self.MPC = 0
        self.MIR = 0
        self.latch_a = 0
        self.latch_b = 0
        self.alu_result = 0
        
        self.sub_cycle = 1 

    def step(self):
        print(f"--- Executando Subciclo {self.sub_cycle} (MPC: {self.MPC}) ---")
        if self.sub_cycle == 1: self._subcycle_1_fetch()
        elif self.sub_cycle == 2: self._subcycle_2_decode_read()
        elif self.sub_cycle == 3: self._subcycle_3_alu()
        elif self.sub_cycle == 4: self._subcycle_4_write_next()
        self.sub_cycle = (self.sub_cycle % 4) + 1

    def _subcycle_1_fetch(self):
        if self.MPC in CONTROL_STORE:
            self.MIR = CONTROL_STORE[self.MPC]
        else:
            print(f"ERRO: Endereço de microcódigo {self.MPC} vazio!")
            self.MIR = 0 

    def _subcycle_2_decode_read(self):
        ctrl = decode_microinstruction(self.MIR)
        self.latch_a = self.regs.get(ctrl['a'], Register("Zero")).read()
        self.latch_b = self.regs.get(ctrl['b'], Register("Zero")).read()

    def _subcycle_3_alu(self):
        ctrl = decode_microinstruction(self.MIR)
        if ctrl['amux'] == 1:
            self.latch_a = self.regs[6].read() # MBR
        
        self.alu_result = self.alu.compute(self.latch_a, self.latch_b, ctrl['alu'], ctrl['sh'])
        print(f"[ULA] {self.latch_a} (op {ctrl['alu']}) {self.latch_b} = {self.alu_result}")

    def _subcycle_4_write_next(self):
        ctrl = decode_microinstruction(self.MIR)
        
        # --- 1. WRITE BACK (Atualizar Registradores) ---
        # Isso deve acontecer ANTES da leitura de memória para o endereço estar certo no MAR
        
        # Escrita explícita no MAR (Bit MAR=1)
        if ctrl['mar']:
            self.regs[5].write(self.alu_result)
            print(f"[WRITE] MAR atualizado para {self.alu_result:04X}")

        # Escrita explícita no MBR (Bit MBR=1)
        if ctrl['mbr']:
            self.regs[6].write(self.alu_result)
            print(f"[WRITE] MBR atualizado para {self.alu_result:04X}")

        # Escrita padrão via Bus C (Bit ENC=1)
        if ctrl['enc']:
            dest_reg = self.regs.get(ctrl['c'])
            if dest_reg:
                dest_reg.write(self.alu_result)
                print(f"[WRITE] Gravado {self.alu_result:04X} em {dest_reg.name}")

        # --- 2. MEMORY ACCESS (Acesso à Memória/Cache) ---
        # Agora que o MAR está atualizado, podemos ler
        
        if ctrl['rd']:
            mar_val = self.regs[5].read()
            # Leitura da Cache (que busca na RAM se precisar)
            data = self.cache.read(mar_val)
            self.regs[6].write(data) # MBR recebe o dado lido
            # Debug para confirmar leitura correta
            # print(f"[MEM] Lido endereço {mar_val}: {data:04X}")
            
        if ctrl['wr']:
            mar_val = self.regs[5].read()
            mbr_val = self.regs[6].read()
            self.cache.write(mar_val, mbr_val)

        # --- 3. NEXT ADDRESS (Decodificação e Pulo) ---
        cond = ctrl['cond']
        next_addr = ctrl['addr']
        
        if cond == 0: # COND_NO
            self.MPC = next_addr
            
        elif cond == 3: # COND_JUMP (Decode)
            # Lê o IR atualizado (pois o Write Back já aconteceu acima)
            ir_val = self.regs[2].read()
            opcode = ir_val & 0xF000 
            
            if opcode in OPCODE_MAP:
                self.MPC = OPCODE_MAP[opcode]
                print(f"[DECODE] Opcode {opcode:04X} -> Saltando para MPC {self.MPC}")
            else:
                print(f"[ERRO] Opcode desconhecido: {opcode:04X}. Parando.")
                self.MPC = 0
                
        else:
            self.MPC = next_addr