# software/assembler.py
from software.isa import OPCODES

class Assembler:
    def __init__(self):
        self.symbol_table = {} # Guarda { "inicio": 0, "loop": 5 }
        self.machine_code = [] # Lista final de números para a RAM

    def assemble(self, filepath):
        """Lê um arquivo .asm e retorna uma lista de inteiros (binário)"""
        
        with open(filepath, 'r') as f:
            lines = f.readlines()

        # --- PASS 1: Mapear Rótulos (Labels) ---
        address_counter = 0
        clean_lines = [] # Guarda linhas limpas para o passo 2

        for line in lines:
            # 1. Limpeza: Remove comentários (#) e espaços extras
            code = line.split('#')[0].strip()
            if not code: continue # Linha vazia

            # 2. Verifica Rótulo (termina com :)
            if code.endswith(':'):
                label_name = code[:-1] # Remove o ':'
                self.symbol_table[label_name] = address_counter
                continue # Rótulo não ocupa espaço na memória, só marca lugar

            # 3. Se tem rótulo na mesma linha da instrução (Ex: "loop: LODD 5")
            if ':' in code:
                label_part, instr_part = code.split(':', 1)
                self.symbol_table[label_part.strip()] = address_counter
                code = instr_part.strip()

            clean_lines.append(code)
            address_counter += 1 # Cada instrução ocupa 1 espaço (16 bits)

        # --- PASS 2: Tradução para Binário ---
        for code in clean_lines:
            parts = code.split()
            mnemonic = parts[0].upper()
            
            # Caso especial: .DATA (Apenas guarda um número)
            if mnemonic == '.DATA':
                value = int(parts[1])
                self.machine_code.append(value)
                continue

            if mnemonic not in OPCODES:
                raise ValueError(f"Instrução desconhecida: {mnemonic}")

            base_opcode = OPCODES[mnemonic]
            operand_val = 0

            # Verifica se tem operando (Ex: LODD 10 ou JUMP inicio)
            if len(parts) > 1:
                operand_str = parts[1]
                
                # Se for um Rótulo conhecido, usa o endereço dele
                if operand_str in self.symbol_table:
                    operand_val = self.symbol_table[operand_str]
                else:
                    # Tenta converter número (suporta decimal e hex 0x...)
                    try:
                        operand_val = int(operand_str, 0)
                    except ValueError:
                        raise ValueError(f"Rótulo ou número inválido: {operand_str}")

            # Combina Opcode + Operando (OR bit a bit)
            # Nota: No MAC-1, opcodes como LODD (0000) somam com endereço (12 bits)
            # INSP/DESP usam 8 bits, mas a lógica de soma funciona igual
            final_instr = base_opcode | (operand_val & 0x0FFF)
            self.machine_code.append(final_instr)

        return self.machine_code