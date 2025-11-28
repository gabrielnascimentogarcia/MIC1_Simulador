# hardware/cpu.py
from hardware.registers import Register, ReadOnlyRegister
from hardware.memory import MainMemory, DirectMappingCache
from hardware.alu import ALU
from software.microcode import CONTROL_STORE, decode_microinstruction, OPCODE_MAP

class CPU:
    def __init__(self):
        self.ram = MainMemory()
        self.cache = DirectMappingCache(self.ram)
        self.alu = ALU()
        
        # Registradores (Com proteção de constantes)
        self.regs = {
            0: Register("None"), 
            1: Register("PC"),
            2: Register("IR"),
            3: Register("SP"),
            4: Register("AC"),
            5: Register("MAR"),
            6: Register("MBR"),
            7: Register("TIR"),
            # Constantes protegidas contra escrita acidental
            8: ReadOnlyRegister("0", 0),
            9: ReadOnlyRegister("+1", 1),
            10: ReadOnlyRegister("-1", -1),
            11: ReadOnlyRegister("AMASK", 0x0FFF),
            12: ReadOnlyRegister("SMASK", 0x00FF),
            # Uso geral
            13: Register("A"),
            14: Register("B"),
            15: Register("C") 
        }
        
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
            print(f"ERRO CRÍTICO: MPC {self.MPC} vazio/inválido!")
            self.MIR = 0 

    def _subcycle_2_decode_read(self):
        ctrl = decode_microinstruction(self.MIR)
        self.latch_a = self.regs.get(ctrl['a'], Register("Zero")).read()
        self.latch_b = self.regs.get(ctrl['b'], Register("Zero")).read()

    def _subcycle_3_alu(self):
        ctrl = decode_microinstruction(self.MIR)
        if ctrl['amux'] == 1:
            self.latch_a = self.regs[6].read() # MBR entra no lado A
        
        self.alu_result = self.alu.compute(self.latch_a, self.latch_b, ctrl['alu'], ctrl['sh'])

    def _subcycle_4_write_next(self):
        ctrl = decode_microinstruction(self.MIR)
        
        # 1. WRITE BACK (Registradores e Memória)
        # Grava nos registradores
        if ctrl['mar']: self.regs[5].write(self.alu_result)
        if ctrl['mbr']: self.regs[6].write(self.alu_result)
        if ctrl['enc']:
            dest = self.regs.get(ctrl['c'])
            if dest: dest.write(self.alu_result)

        # Acesso à Memória (Realizado após atualizar MAR/MBR)
        if ctrl['rd']:
            # Lê da Cache usando o endereço que está no MAR
            data = self.cache.read(self.regs[5].read())
            self.regs[6].write(data) # Joga no MBR
            
        if ctrl['wr']:
            # Escreve na Cache o dado do MBR no endereço do MAR
            self.cache.write(self.regs[5].read(), self.regs[6].read())

        # 2. NEXT ADDRESS (Lógica de Branching JAM)
        cond = ctrl['cond']
        next_addr = ctrl['addr']
        
        # O bit alto (256) é ativado se a condição for verdadeira
        high_bit = 0
        
        if cond == 0: # Sem pulo condicional
            high_bit = 0
            
        elif cond == 1: # JAM N (Pula se Negativo)
            if self.alu.n_flag: high_bit = 0x100
            
        elif cond == 2: # JAM Z (Pula se Zero)
            if self.alu.z_flag: high_bit = 0x100
            
        elif cond == 3: # JAM JUMP (Decodificação de Instrução)
            ir = self.regs[2].read()
            
            # Lógica para instruções normais e estendidas (0xF...)
            if (ir & 0xF000) == 0xF000:
                # Instruções estendidas usam os 8 bits superiores (ex: F400)
                opcode = ir & 0xFF00
            else:
                # Instruções normais usam os 4 bits superiores
                opcode = ir & 0xF000
            
            if opcode in OPCODE_MAP:
                self.MPC = OPCODE_MAP[opcode]
                print(f"[DECODE] IR={ir:04X} -> Opcode {opcode:04X} -> Salto para MPC {self.MPC}")
                return # Sai pois já definimos o MPC via mapa
            else:
                print(f"[ERRO] Opcode desconhecido: {opcode:04X}")
                self.MPC = 0
                return

        # Combina o endereço base com o bit alto (JAM)
        self.MPC = next_addr | high_bit