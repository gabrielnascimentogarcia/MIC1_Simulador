# software/microcode.py

# --- Mapeamento de Bits ---
R_MASK = {
    'None': 0, 'PC': 1, 'IR': 2, 'SP': 3, 'AC': 4, 'MAR': 5, 'MBR': 6,
    'TIR': 7, '0': 8, '+1': 9, '-1': 10, 'AMASK': 11, 'SMASK': 12,
    'A': 13, 'B': 14, 'C': 15 
}

# Constantes
ALU_ADD, ALU_AND, ALU_A, ALU_NOT = 0, 1, 2, 3
SH_NO, SH_SRA, SH_SLL8 = 0, 1, 2
COND_NO, COND_N, COND_Z, COND_JUMP = 0, 1, 2, 3

def create_uinst(addr_next, 
                 amux=0, cond=COND_NO, alu=ALU_A, sh=SH_NO, 
                 mbr=0, mar=0, rd=0, wr=0, enc=0, 
                 c='None', b='None', a='None'):
    
    val_c = R_MASK.get(c, 0)
    val_b = R_MASK.get(b, 0)
    val_a = R_MASK.get(a, 0)
    
    # Layout de Bits
    uinst = 0
    uinst |= (addr_next & 0x1FF)       # 0-8
    uinst |= (val_a & 0xF) << 9        # 9-12
    uinst |= (val_b & 0xF) << 13       # 13-16
    uinst |= (val_c & 0xF) << 17       # 17-20
    uinst |= (enc   & 1)   << 21       # 21
    uinst |= (wr    & 1)   << 22       # 22
    uinst |= (rd    & 1)   << 23       # 23
    uinst |= (mar   & 1)   << 24       # 24
    uinst |= (mbr   & 1)   << 25       # 25
    uinst |= (sh    & 3)   << 26       # 26-27
    uinst |= (alu   & 3)   << 28       # 28-29
    uinst |= (cond  & 3)   << 30       # 30-31
    uinst |= (amux  & 1)   << 32       # 32
    
    return uinst

def decode_microinstruction(instr):
    return {
        'addr': instr & 0x1FF,
        'a':    (instr >> 9)  & 0xF,
        'b':    (instr >> 13) & 0xF,
        'c':    (instr >> 17) & 0xF,
        'enc':  (instr >> 21) & 1,
        'wr':   (instr >> 22) & 1,
        'rd':   (instr >> 23) & 1,
        'mar':  (instr >> 24) & 1,
        'mbr':  (instr >> 25) & 1,
        'sh':   (instr >> 26) & 0x3,
        'alu':  (instr >> 28) & 0x3,
        'cond': (instr >> 30) & 0x3,
        'amux': (instr >> 32) & 1
    }

# --- MEMÓRIA DE CONTROLE ---
CONTROL_STORE = {}

# 1. FETCH CYCLE
# 0: MAR := PC; RD;
CONTROL_STORE[0] = create_uinst(addr_next=1, mar=1, rd=1, b='PC', alu=ALU_ADD)
# 1: PC := PC + 1; RD;
CONTROL_STORE[1] = create_uinst(addr_next=2, rd=1, enc=1, c='PC', b='PC', a='+1', alu=ALU_ADD)
# 2: IR := MBR; Goto [DECODE]
CONTROL_STORE[2] = create_uinst(addr_next=0, cond=COND_JUMP, enc=1, c='IR', b='MBR', alu=ALU_ADD)


# --- INSTRUÇÕES ---

# LODD (0000)
# 6: MAR := IR & AMASK; RD;  <-- MUDANÇA: Usa AND com AMASK
CONTROL_STORE[6] = create_uinst(addr_next=7, mar=1, rd=1, b='IR', a='AMASK', alu=ALU_AND)
# 7: RD;
CONTROL_STORE[7] = create_uinst(addr_next=8, rd=1)
# 8: AC := MBR;
CONTROL_STORE[8] = create_uinst(addr_next=0, enc=1, c='AC', b='MBR', alu=ALU_ADD)

# STOD (0001)
# 9: MAR := IR & AMASK; <-- MUDANÇA
CONTROL_STORE[9] = create_uinst(addr_next=10, mar=1, b='IR', a='AMASK', alu=ALU_AND)
# 10: MBR := AC; WR;
CONTROL_STORE[10] = create_uinst(addr_next=11, mbr=1, wr=1, b='AC', alu=ALU_ADD)
# 11: WR;
CONTROL_STORE[11] = create_uinst(addr_next=0, wr=1)

# ADDD (0010)
# 12: MAR := IR & AMASK; RD; <-- MUDANÇA
CONTROL_STORE[12] = create_uinst(addr_next=13, mar=1, rd=1, b='IR', a='AMASK', alu=ALU_AND)
# 13: RD;
CONTROL_STORE[13] = create_uinst(addr_next=14, rd=1)
# 14: AC := AC + MBR;
CONTROL_STORE[14] = create_uinst(addr_next=0, enc=1, c='AC', b='AC', amux=1, alu=ALU_ADD)

# JUMP (0110)
# 26: PC := IR & AMASK; <-- MUDANÇA
CONTROL_STORE[26] = create_uinst(addr_next=0, enc=1, c='PC', b='IR', a='AMASK', alu=ALU_AND)

# MAPA
OPCODE_MAP = {
    0x0000: 6,
    0x1000: 9,
    0x2000: 12,
    0x6000: 26
}