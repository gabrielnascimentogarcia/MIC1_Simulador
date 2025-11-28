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
        
        # Registradores
        self.regs = {
            0: Register("None"), # Dummy
            1: Register("PC"),
            2: Register("IR"),
            3: Register("SP"),
            4: Register("AC"),
            5: Register("MAR"),
            6: Register("MBR"),
            7: Register("TIR"),
            # CONSTANTES BLINDADAS
            8: ReadOnlyRegister("0", 0),
            9: ReadOnlyRegister("+1", 1),
            10: ReadOnlyRegister("-1", -1),
            11: ReadOnlyRegister("AMASK", 0x0FFF),
            12: ReadOnlyRegister("SMASK", 0x00FF),
            # Uso Geral
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
            print(f"ERRO CRÍTICO: MPC {self.MPC} vazio!")
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

    def _subcycle_4_write_next(self):
        ctrl = decode_microinstruction(self.MIR)
        
        # 1. WRITE BACK
        if ctrl['mar']: self.regs[5].write(self.alu_result)
        if ctrl['mbr']: self.regs[6].write(self.alu_result)
        if ctrl['enc']:
            dest = self.regs.get(ctrl['c'])
            if dest: 
                dest.write(self.alu_result)
                print(f"[WRITE] {dest.name} <- {self.alu_result:04X}")

        # 2. MEMORY
        if ctrl['rd']:
            data = self.cache.read(self.regs[5].read())
            self.regs[6].write(data)
        if ctrl['wr']:
            self.cache.write(self.regs[5].read(), self.regs[6].read())

        # 3. NEXT ADDRESS (Com lógica de JAM correta)
        cond = ctrl['cond']
        next_addr = ctrl['addr']
        
        # O bit alto do próximo endereço (bit 8, valor 256) é determinado pela condição
        high_bit = 0
        
        if cond == 0: # Sem pulo
            high_bit = 0
        elif cond == 1: # JAM N (Pula se Negativo)
            if self.alu.n_flag: high_bit = 0x100
        elif cond == 2: # JAM Z (Pula se Zero)
            if self.alu.z_flag: high_bit = 0x100
        elif cond == 3: # JAM JUMP (Decode)
            ir = self.regs[2].read()
            opcode = ir & 0xF000
            if opcode == 0xF000: opcode = ir & 0xFF00 # Instruções estendidas
            
            if opcode in OPCODE_MAP:
                self.MPC = OPCODE_MAP[opcode]
                print(f"[DECODE] IR={ir:04X} Op={opcode:04X} -> MPC {self.MPC}")
                return # Sai direto pois já definimos o MPC
            else:
                print(f"[ERRO] Opcode inválido {opcode:04X}")
                self.MPC = 0
                return

        self.MPC = next_addr | high_bit