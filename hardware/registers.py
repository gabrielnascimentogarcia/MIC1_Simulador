# hardware/registers.py
from config import MASK_16BIT

class Register:
    def __init__(self, name, value=0):
        self.name = name
        self._value = value & MASK_16BIT

    def write(self, value):
        """Grava um valor garantindo que fique em 16 bits (Overflow)"""
        self._value = value & MASK_16BIT

    def read(self):
        """Lê o valor cru (unsigned)"""
        return self._value

    def read_signed(self):
        """Lê o valor como inteiro com sinal (Complemento de 2)"""
        if self._value & 0x8000: # Se o bit 15 for 1
            return self._value - 0x10000
        return self._value

    def __str__(self):
        return f"[{self.name}: {self._value:04X}]"

class ReadOnlyRegister(Register):
    """Registrador que ignora escritas (para constantes como 0, +1, AMASK)"""
    def write(self, value):
        # Ignora silenciosamente ou pode logar um aviso se quiser debugar
        # print(f"[WARN] Tentativa de escrita no registrador constante {self.name} ignorada.")
        pass