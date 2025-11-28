# main.py
from hardware.cpu import CPU
from software.assembler import Assembler
import os

def main():
    print("--- Montador e Simulador MIC-1 ---")
    
    # 1. Montagem (Assembler)
    asm_file = "programs/teste_soma.asm"
    
    if not os.path.exists(asm_file):
        print(f"ERRO: Crie o arquivo {asm_file} primeiro!")
        return

    print(f"Montando {asm_file}...")
    assembler = Assembler()
    program_bin = assembler.assemble(asm_file)
    
    print(f"Binário gerado ({len(program_bin)} palavras):")
    # Mostra em Hexa para conferirmos
    print([hex(x) for x in program_bin]) 
    
    # 2. Inicialização da CPU
    print("\nIniciando CPU e Carregando Memória...")
    cpu = CPU()
    
    # Carrega o programa na RAM (Endereço 0 em diante)
    for addr, value in enumerate(program_bin):
        cpu.ram.write(addr, value)
        
    # 3. Execução
    print("\nRodando Simulação (Pressione Enter)...")
    # Vamos rodar ciclos suficientes para fazer a soma
    # JUMP(start) -> LODD -> ADDD -> STOD -> JUMP(end)
    
    for i in range(200): # 60 subciclos deve dar para ver algo acontecendo
        cpu.step()
        
        # Debug: Mostrar registradores importantes a cada passo
        pc = cpu.regs[1].read()
        ac = cpu.regs[4].read()
        ir = cpu.regs[2].read()
        print(f"   [Estado] PC={pc} AC={ac} IR={ir:04X}")
        
        # Pausa opcional (comente se quiser rodar direto)
        # input() 

    # 4. Verificação Final
    # O resultado (15 + 25 = 40) deve estar na variável var_c
    # var_c é a 3ª posição de dados, mas tem o JUMP inicial (addr 0).
    # Estrutura: 0:JUMP, 1:var_a, 2:var_b, 3:var_c
    res_addr = 3 
    resultado = cpu.ram.read(res_addr)
    print(f"\n--- FIM ---")
    print(f"Resultado na Memória[{res_addr}]: {resultado} (Esperado: 40)")

if __name__ == "__main__":
    main()