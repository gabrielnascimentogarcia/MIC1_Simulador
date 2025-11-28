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

# FETCH
CONTROL_STORE[0] = create_uinst(addr_next=1, mar=1, rd=1, b='PC', alu=ALU_ADD)
CONTROL_STORE[1] = create_uinst(addr_next=2, enc=1, c='PC', b='PC', a='+1', alu=ALU_ADD)
CONTROL_STORE[2] = create_uinst(addr_next=0, cond=COND_JUMP, enc=1, c='IR', b='MBR', alu=ALU_ADD)

# --- INSTRUÇÕES ---

# LODD (0000)
CONTROL_STORE[6] = create_uinst(addr_next=7, mar=1, rd=1, b='IR', a='AMASK', alu=ALU_AND)
CONTROL_STORE[7] = create_uinst(addr_next=8, rd=1)
CONTROL_STORE[8] = create_uinst(addr_next=0, enc=1, c='AC', b='MBR', alu=ALU_ADD)

# STOD (0001)
CONTROL_STORE[9] = create_uinst(addr_next=10, mar=1, b='IR', a='AMASK', alu=ALU_AND)
CONTROL_STORE[10] = create_uinst(addr_next=11, mbr=1, wr=1, b='AC', alu=ALU_ADD)
CONTROL_STORE[11] = create_uinst(addr_next=0, wr=1)

# ADDD (0010)
CONTROL_STORE[12] = create_uinst(addr_next=13, mar=1, rd=1, b='IR', a='AMASK', alu=ALU_AND)
CONTROL_STORE[13] = create_uinst(addr_next=14, rd=1)
CONTROL_STORE[14] = create_uinst(addr_next=0, enc=1, c='AC', b='AC', amux=1, alu=ALU_ADD)

# SUBD (0011) - AC - MBR (Complemento de 2)
CONTROL_STORE[15] = create_uinst(addr_next=16, mar=1, rd=1, b='IR', a='AMASK', alu=ALU_AND)
CONTROL_STORE[16] = create_uinst(addr_next=17, rd=1)
CONTROL_STORE[17] = create_uinst(addr_next=18, enc=1, c='A', amux=1, alu=ALU_NOT) # A = ~MBR
CONTROL_STORE[18] = create_uinst(addr_next=19, enc=1, c='AC', b='AC', a='+1', alu=ALU_ADD) # AC+1
CONTROL_STORE[19] = create_uinst(addr_next=0, enc=1, c='AC', b='AC', a='A', alu=ALU_ADD) # AC + ~MBR

# JPOS (0100) - Jump if AC >= 0 (N=0)
# Passo 1: Recalcular flags (ALU = AC)
# Se N=1 (Negativo), JAMN vai jogar para endereço 20 + 256 = 276.
# Se N=0 (Positivo), vai para 20 + 0 = 20.
# Queremos pular se N=0. Então o MPC 20 deve fazer o Jump. O MPC 276 deve abortar.
CONTROL_STORE[20] = create_uinst(addr_next=21, b='AC', alu=ALU_A, cond=COND_N)
# Caminho POSITIVO (N=0, Jump Taken)
CONTROL_STORE[21] = create_uinst(addr_next=0, enc=1, c='PC', b='IR', a='AMASK', alu=ALU_AND) 
# Caminho NEGATIVO (N=1, Jump Not Taken -> MPC 276 (20|0x100))
# Como addr_next em 20 era 21, se N=1, ele vai para 21 | 0x100 = 277?
# Não, o hardware faz: MPC = addr_next | (0x100 if N else 0).
# Se addr_next é 21. Se N=1, vai para 21 + 256 = 277.
CONTROL_STORE[277] = create_uinst(addr_next=0) # Aborta (não pula)

# JZER (0101) - Jump if Zero (Z=1)
# Recalcula Flags
CONTROL_STORE[23] = create_uinst(addr_next=24, b='AC', alu=ALU_A, cond=COND_Z)
# Caminho NÃO ZERO (Z=0, Jump Not Taken) -> Vai para 24
CONTROL_STORE[24] = create_uinst(addr_next=0) # Aborta
# Caminho ZERO (Z=1, Jump Taken) -> Vai para 24 | 0x100 = 280
CONTROL_STORE[280] = create_uinst(addr_next=0, enc=1, c='PC', b='IR', a='AMASK', alu=ALU_AND)

# JUMP (0110)
CONTROL_STORE[26] = create_uinst(addr_next=0, enc=1, c='PC', b='IR', a='AMASK', alu=ALU_AND)

# LOCO (0111)
CONTROL_STORE[27] = create_uinst(addr_next=0, enc=1, c='AC', b='IR', a='AMASK', alu=ALU_AND)

# JNEG (1100) - Jump if Negative (N=1)
CONTROL_STORE[28] = create_uinst(addr_next=29, b='AC', alu=ALU_A, cond=COND_N)
# Caminho POSITIVO (N=0) -> Vai para 29
CONTROL_STORE[29] = create_uinst(addr_next=0) # Aborta
# Caminho NEGATIVO (N=1) -> Vai para 29 | 0x100 = 285
CONTROL_STORE[285] = create_uinst(addr_next=0, enc=1, c='PC', b='IR', a='AMASK', alu=ALU_AND)

# JNZE (1101) - Jump if Not Zero (Z=0)
CONTROL_STORE[30] = create_uinst(addr_next=31, b='AC', alu=ALU_A, cond=COND_Z)
# Caminho NÃO ZERO (Z=0) -> Vai para 31 (Jump Taken)
CONTROL_STORE[31] = create_uinst(addr_next=0, enc=1, c='PC', b='IR', a='AMASK', alu=ALU_AND)
# Caminho ZERO (Z=1) -> Vai para 31 | 0x100 = 287 (Jump Not Taken)
CONTROL_STORE[287] = create_uinst(addr_next=0)

# Mapeamento
OPCODE_MAP = {
    0x0000: 6, 0x1000: 9, 0x2000: 12, 0x3000: 15,
    0x4000: 20, 0x5000: 23, 0x6000: 26, 0x7000: 27,
    0xC000: 28, 0xD000: 30
}