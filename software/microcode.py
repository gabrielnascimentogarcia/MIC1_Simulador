# software/microcode.py

R_MASK = {
    'None': 0, 'PC': 1, 'IR': 2, 'SP': 3, 'AC': 4, 'MAR': 5, 'MBR': 6,
    'TIR': 7, '0': 8, '+1': 9, '-1': 10, 'AMASK': 11, 'SMASK': 12,
    'A': 13, 'B': 14, 'C': 15 
}

ALU_ADD, ALU_AND, ALU_A, ALU_NOT = 0, 1, 2, 3
SH_NO, SH_SRA, SH_SLL8 = 0, 1, 2
COND_NO, COND_N, COND_Z, COND_JUMP = 0, 1, 2, 3

def create_uinst(addr_next, amux=0, cond=COND_NO, alu=ALU_A, sh=SH_NO, 
                 mbr=0, mar=0, rd=0, wr=0, enc=0, c='None', b='None', a='None'):
    val_c = R_MASK.get(c, 0); val_b = R_MASK.get(b, 0); val_a = R_MASK.get(a, 0)
    uinst = 0
    uinst |= (addr_next & 0x1FF)
    uinst |= (val_a & 0xF) << 9
    uinst |= (val_b & 0xF) << 13
    uinst |= (val_c & 0xF) << 17
    uinst |= (enc & 1)<<21; uinst |= (wr & 1)<<22; uinst |= (rd & 1)<<23
    uinst |= (mar & 1)<<24; uinst |= (mbr & 1)<<25
    uinst |= (sh & 3)<<26; uinst |= (alu & 3)<<28; uinst |= (cond & 3)<<30; uinst |= (amux & 1)<<32
    return uinst

def decode_microinstruction(instr):
    return {'addr': instr&0x1FF, 'a':(instr>>9)&0xF, 'b':(instr>>13)&0xF, 'c':(instr>>17)&0xF,
            'enc':(instr>>21)&1, 'wr':(instr>>22)&1, 'rd':(instr>>23)&1, 'mar':(instr>>24)&1,
            'mbr':(instr>>25)&1, 'sh':(instr>>26)&3, 'alu':(instr>>28)&3, 'cond':(instr>>30)&3, 'amux':(instr>>32)&1}

CONTROL_STORE = {}

# --- FETCH CYCLE (Otimizado) ---
# 0: MAR := PC; RD
CONTROL_STORE[0] = create_uinst(addr_next=1, mar=1, rd=1, b='PC', alu=ALU_ADD)
# 1: PC := PC + 1; (RD removido pois a memória já está lendo)
CONTROL_STORE[1] = create_uinst(addr_next=2, enc=1, c='PC', b='PC', a='+1', alu=ALU_ADD)
# 2: IR := MBR; Goto DECODE
CONTROL_STORE[2] = create_uinst(addr_next=0, cond=COND_JUMP, enc=1, c='IR', b='MBR', alu=ALU_ADD)

# --- INSTRUÇÕES BÁSICAS ---

# LODD (0000)
CONTROL_STORE[6] = create_uinst(addr_next=7, mar=1, rd=1, b='IR', a='AMASK', alu=ALU_AND)
CONTROL_STORE[7] = create_uinst(addr_next=8, rd=1)
CONTROL_STORE[8] = create_uinst(addr_next=0, enc=1, c='AC', b='MBR', alu=ALU_ADD)

# STOD (0001)
CONTROL_STORE[9] = create_uinst(addr_next=10, mar=1, b='IR', a='AMASK', alu=ALU_AND)
CONTROL_STORE[10] = create_uinst(addr_next=11, mbr=1, wr=1, b='AC', alu=ALU_ADD)
CONTROL_STORE[11] = create_uinst(addr_next=0, wr=1) # Ciclo extra para garantir escrita

# ADDD (0010)
CONTROL_STORE[12] = create_uinst(addr_next=13, mar=1, rd=1, b='IR', a='AMASK', alu=ALU_AND)
CONTROL_STORE[13] = create_uinst(addr_next=14, rd=1)
CONTROL_STORE[14] = create_uinst(addr_next=0, enc=1, c='AC', b='AC', amux=1, alu=ALU_ADD)

# SUBD (0011) - Implementação: AC = AC - MBR
# Usamos Compl. de 2: AC = AC + (~MBR + 1)
CONTROL_STORE[15] = create_uinst(addr_next=16, mar=1, rd=1, b='IR', a='AMASK', alu=ALU_AND)
CONTROL_STORE[16] = create_uinst(addr_next=17, rd=1)
# Passo 1: A := NOT MBR (Guarda ~MBR no reg A temporário)
CONTROL_STORE[17] = create_uinst(addr_next=18, enc=1, c='A', amux=1, alu=ALU_NOT) 
# Passo 2: AC := AC + 1 (Adiciona 1 ao acumulador)
CONTROL_STORE[18] = create_uinst(addr_next=19, enc=1, c='AC', b='AC', a='+1', alu=ALU_ADD)
# Passo 3: AC := AC + A (Soma o ~MBR)
CONTROL_STORE[19] = create_uinst(addr_next=0, enc=1, c='AC', b='AC', a='A', alu=ALU_ADD)

# --- SALTOS (Com recálculo de flags) ---

# JPOS (0100) - Jump if AC >= 0
# Passo 1: Passa AC pela ULA para setar flags N e Z corretamente
CONTROL_STORE[20] = create_uinst(addr_next=21, b='AC', alu=ALU_A, cond=COND_N)
# Se N=1 (Negativo), JAM ativa bit 256 -> Vai para 20|0x100 = 277 (Não pula)
# Se N=0 (Positivo), Vai para 21 (Pula)
CONTROL_STORE[21] = create_uinst(addr_next=0, enc=1, c='PC', b='IR', a='AMASK', alu=ALU_AND) # Pula
CONTROL_STORE[277] = create_uinst(addr_next=0) # Não pula, volta pro início

# JZER (0101) - Jump if Zero
CONTROL_STORE[23] = create_uinst(addr_next=24, b='AC', alu=ALU_A, cond=COND_Z)
# Se Z=1, vai para 24|0x100 = 280 (Pula)
# Se Z=0, vai para 24 (Não pula)
CONTROL_STORE[24] = create_uinst(addr_next=0) # Não pula
CONTROL_STORE[280] = create_uinst(addr_next=0, enc=1, c='PC', b='IR', a='AMASK', alu=ALU_AND) # Pula

# JUMP (0110)
CONTROL_STORE[26] = create_uinst(addr_next=0, enc=1, c='PC', b='IR', a='AMASK', alu=ALU_AND)

# LOCO (0111)
CONTROL_STORE[27] = create_uinst(addr_next=0, enc=1, c='AC', b='IR', a='AMASK', alu=ALU_AND)

# JNEG (1100) - Jump if Negative
CONTROL_STORE[28] = create_uinst(addr_next=29, b='AC', alu=ALU_A, cond=COND_N)
# Se N=1, vai para 285 (Pula)
# Se N=0, vai para 29 (Não pula)
CONTROL_STORE[29] = create_uinst(addr_next=0)
CONTROL_STORE[285] = create_uinst(addr_next=0, enc=1, c='PC', b='IR', a='AMASK', alu=ALU_AND)

# JNZE (1101) - Jump if Not Zero
CONTROL_STORE[30] = create_uinst(addr_next=31, b='AC', alu=ALU_A, cond=COND_Z)
# Se Z=1, vai para 287 (Não pula)
# Se Z=0, vai para 31 (Pula)
CONTROL_STORE[31] = create_uinst(addr_next=0, enc=1, c='PC', b='IR', a='AMASK', alu=ALU_AND)
CONTROL_STORE[287] = create_uinst(addr_next=0)


# --- INSTRUÇÕES DE PILHA E ESTENDIDAS (F...) ---

# PUSH (F400) - SP := SP - 1; M[SP] := AC
CONTROL_STORE[35] = create_uinst(addr_next=36, enc=1, c='SP', b='SP', a='-1', alu=ALU_ADD)
CONTROL_STORE[36] = create_uinst(addr_next=37, mar=1, b='SP', alu=ALU_ADD) # MAR = SP
CONTROL_STORE[37] = create_uinst(addr_next=38, mbr=1, wr=1, b='AC', alu=ALU_ADD) # MBR = AC; WR
CONTROL_STORE[38] = create_uinst(addr_next=0, wr=1)

# POP (F600) - AC := M[SP]; SP := SP + 1
CONTROL_STORE[39] = create_uinst(addr_next=40, mar=1, b='SP', alu=ALU_ADD)
CONTROL_STORE[40] = create_uinst(addr_next=41, rd=1)
CONTROL_STORE[41] = create_uinst(addr_next=42, enc=1, c='AC', b='MBR', alu=ALU_ADD) # AC = MBR
CONTROL_STORE[42] = create_uinst(addr_next=0, enc=1, c='SP', b='SP', a='+1', alu=ALU_ADD) # SP++

# --- MAPEAMENTO ---
OPCODE_MAP = {
    0x0000: 6, 0x1000: 9, 0x2000: 12, 0x3000: 15, # Básicas
    0x4000: 20, 0x5000: 23, 0x6000: 26, 0x7000: 27, # Saltos/LOCO
    0xC000: 28, 0xD000: 30, # Mais Saltos
    0xF400: 35, # PUSH
    0xF600: 39  # POP
}