# programs/teste_complexo.asm
# Teste de Pilha, Subtração e Flags (JNEG)
# Objetivo: 10 - 20 = -10 -> Deve ativar flag N e pular.

JUMP inicio

# --- Dados ---
val_1:  .DATA 0     # Vai receber 20
val_2:  .DATA 0     # Vai receber 10
res:    .DATA 0     # Vai receber -10 (0xFFF6)
status: .DATA 0     # 0 = Falha, 1 = Sucesso

# --- Código ---
inicio:
    # 1. Teste de Pilha (LIFO - Last In, First Out)
    LOCO 10         # AC = 10
    PUSH            # Empilha 10 (SP decrementa)
    
    LOCO 20         # AC = 20
    PUSH            # Empilha 20 (SP decrementa)
    
    # Agora vamos tirar. O primeiro a sair deve ser o 20.
    POP             # AC = 20
    STOD val_1      # Guarda na memória
    
    POP             # AC = 10
    STOD val_2      # Guarda na memória
    
    # 2. Teste de Subtração (SUBD)
    # Vamos fazer: 10 - 20 = -10
    LODD val_2      # AC = 10
    SUBD val_1      # AC = AC - 20
    STOD res        # Deve salvar 0xFFF6 (-10)
    
    # 3. Teste de Flags e JNEG
    # O AC está com -10. A flag N deve estar ligada.
    JNEG sucesso    # Se funcionar, pula para o label 'sucesso'
    
    # Se não pular, caiu aqui (FALHA)
    LOCO 0
    STOD status
    JUMP fim

sucesso:
    LOCO 1          # Carrega 1 para indicar sucesso
    STOD status

fim:
    JUMP fim        # Loop infinito