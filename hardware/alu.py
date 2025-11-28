# hardware/alu.py
from config import MASK_16BIT

class ALU:
    def __init__(self):
        # Flags de estado (importante para os saltos condicionais como JNEG, JZER)
        self.n_flag = False # Negative
        self.z_flag = False # Zero

    def compute(self, a, b, alu_control, shift_control):
        """
        Executa a operação da ULA e depois passa pelo Deslocador.
        a, b: Valores de entrada (16 bits)
        alu_control: 2 bits (00=ADD, 01=AND, 10=A, 11=NOT A)
        shift_control: 2 bits (00=None, 01=SRA1, 10=SLL8)
        """
        
        # 1. Operação da ULA
        res = 0
        if alu_control == 0:   # A + B
            res = a + b
        elif alu_control == 1: # A AND B
            res = a & b
        elif alu_control == 2: # A (Pass through)
            res = a
        elif alu_control == 3: # NOT A (Inverso)
            res = ~a
        
        # Garante 16 bits após a conta (ex: soma estourou)
        res = res & MASK_16BIT

        # 2. Operação do Deslocador (Shifter)
        # O shifter pega o resultado da ULA e mexe nos bits
        if shift_control == 0:   # Sem deslocamento
            pass 
        elif shift_control == 1: # SRA 1 (Shift Right Arithmetic - mantém sinal)
            # Simulação de bit de sinal para SRA
            sign_bit = res & 0x8000
            res = (res >> 1)
            if sign_bit: res |= 0x8000 # Mantém o negativo se era negativo
        elif shift_control == 2: # SLL 8 (Shift Left Logical 8 bits)
            res = (res << 8) & MASK_16BIT
        
        # 3. Atualiza Flags (Baseado no resultado FINAL)
        self.z_flag = (res == 0)
        self.n_flag = (res & 0x8000) != 0 # Se bit 15 é 1, é negativo
        
        return res