# programs/teste_soma.asm
# Programa Simples: Soma A + B e guarda em C

# --- Dados ---
# Vamos pular as primeiras posições para o código
JUMP inicio

# Variáveis (Endereços 1, 2, 3)
var_a: .DATA 15    # Valor 15
var_b: .DATA 25    # Valor 25
var_c: .DATA 0     # Resultado

# --- Código ---
inicio:
    LODD var_a     # Carrega A no AC (Acumulador)
    ADDD var_b     # Soma B com AC
    STOD var_c     # Guarda AC em C
    
fim:
    JUMP fim       # Loop infinito para parar