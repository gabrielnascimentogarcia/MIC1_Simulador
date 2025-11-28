# main.py
from hardware.cpu import CPU
from software.assembler import Assembler
import os

def main():
    print("--- Montador e Simulador MIC-1 (Modo Texto) ---")
    
    # 1. MUDANÇA AQUI: Apontar para o teste complexo
    asm_file = "programs/teste_complexo.asm"
    
    if not os.path.exists(asm_file):
        print(f"ERRO: Crie o arquivo {asm_file} primeiro!")
        return

    print(f"Montando {asm_file}...")
    assembler = Assembler()
    program_bin = assembler.assemble(asm_file)
    
    print(f"Binário gerado ({len(program_bin)} palavras):")
    print([hex(x) for x in program_bin]) 
    
    print("\nIniciando CPU e Carregando Memória...")
    cpu = CPU()
    
    for addr, value in enumerate(program_bin):
        cpu.ram.write(addr, value)
        
    print("\nRodando Simulação (Aguarde)...")
    
    # Rodamos 200 ciclos para garantir que dê tempo de fazer todas as operações
    for i in range(1000): 
        cpu.step()
        # Se quiser ver o log detalhado, descomente abaixo, mas vai ficar grande:
        # pc = cpu.regs[1].read()
        # print(f"   [Ciclo {i}] PC={pc} AC={cpu.regs[4].read():04X}")

    # 4. MUDANÇA AQUI: Verificação do Resultado
    # No teste_complexo.asm:
    # Endereço 3 (res) deve ser -10 (0xFFF6)
    # Endereço 4 (status) deve ser 1 (Sucesso)
    
    val_res = cpu.ram.read(3)
    val_status = cpu.ram.read(4)
    
    print(f"\n--- RESULTADO FINAL ---")
    print(f"Variável 'res'    (End 3): {val_res:04X} (Esperado: FFF6 [-10])")
    print(f"Variável 'status' (End 4): {val_status}    (Esperado: 1 [Sucesso])")

    if val_status == 1:
        print("\n>>> SUCESSO! A CPU passou no teste de estresse! <<<")
    else:
        print("\n>>> FALHA! O salto condicional ou a subtração não funcionaram. <<<")

if __name__ == "__main__":
    main()