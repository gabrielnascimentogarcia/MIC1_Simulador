# hardware/memory.py
from config import MEMORY_SIZE, CACHE_SIZE, BLOCK_SIZE, MASK_16BIT

class MainMemory:
    def __init__(self):
        # A memória é apenas uma lista gigante de zeros inicialmente
        self._data = [0] * MEMORY_SIZE

    def read(self, addr):
        """Lê uma palavra da memória. Se o endereço for inválido, retorna 0."""
        if 0 <= addr < len(self._data):
            return self._data[addr]
        return 0

    def write(self, addr, value):
        """Escreve na memória (garantindo 16 bits)"""
        if 0 <= addr < len(self._data):
            self._data[addr] = value & MASK_16BIT

    def get_block(self, start_addr):
        """
        Simula a leitura em 'burst' (bloco) para a Cache.
        Retorna uma lista de palavras (ex: 4 palavras).
        """
        block = []
        for i in range(BLOCK_SIZE):
            # Pega o dado ou 0 se sair fora da memória
            if start_addr + i < len(self._data):
                block.append(self._data[start_addr + i])
            else:
                block.append(0)
        return block

# --- Estrutura da Cache ---

class CacheLine:
    def __init__(self):
        self.valid = False  # V: Bit de validade
        self.tag = 0        # TAG: Etiqueta
        # Dados: Guarda o bloco inteiro (ex: lista de 4 números)
        self.data = [0] * BLOCK_SIZE 

class DirectMappingCache:
    def __init__(self, main_memory):
        self.ram = main_memory
        # Cria as linhas da cache (ex: 16 linhas)
        self.lines = [CacheLine() for _ in range(CACHE_SIZE)]
        
        # Estatísticas para mostrar na tela depois
        self.last_access_status = "IDLE" # "HIT" ou "MISS"

    def _split_address(self, addr):
        """
        Matemática do Endereço:
        Endereço (12 bits) = [ TAG (6b) | INDEX (4b) | OFFSET (2b) ]
        """
        # 1. Offset: Pega os últimos 2 bits (para blocos de 4 palavras)
        # 3 em binário é 11 (máscara de 2 bits)
        offset = addr & 0x03 
        
        # 2. Index: Joga fora os 2 bits do offset e pega os próximos 4
        # 15 em binário é 1111 (máscara de 4 bits para 16 linhas)
        index = (addr >> 2) & 0x0F
        
        # 3. Tag: Joga fora os 6 bits (2 do offset + 4 do index) e pega o resto
        tag = addr >> 6
        
        return tag, index, offset

    def read(self, addr):
        tag, index, offset = self._split_address(addr)
        line = self.lines[index]

        # Verifica se é HIT
        if line.valid and line.tag == tag:
            self.last_access_status = "HIT"
            print(f"[CACHE] Read Hit! Endereço {addr} (Linha {index})")
            return line.data[offset]
        
        # Se não, é MISS
        self.last_access_status = "MISS"
        print(f"[CACHE] Read Miss! Buscando bloco na RAM...")
        
        # Calcula onde começa o bloco na RAM (zera os bits do offset)
        block_start_addr = addr - offset
        
        # Busca o bloco inteiro na RAM
        new_block = self.ram.get_block(block_start_addr)
        
        # Atualiza a linha da Cache
        line.valid = True
        line.tag = tag
        line.data = new_block
        
        return line.data[offset]

    def write(self, addr, value):
        """
        Política: Write-Through (Escreve na Cache e na RAM ao mesmo tempo)
        """
        # 1. Escreve na RAM sempre (segurança)
        self.ram.write(addr, value)
        
        # 2. Verifica se o dado está na cache para atualizar lá também
        tag, index, offset = self._split_address(addr)
        line = self.lines[index]
        
        # Só atualizamos a cache se for um Write Hit (já estava lá)
        # Se for Write Miss, no Write-Through simples, não precisamos carregar.
        if line.valid and line.tag == tag:
            line.data[offset] = value & MASK_16BIT
            print(f"[CACHE] Write Hit! Atualizado Cache e RAM no end {addr}")
        else:
            print(f"[CACHE] Write Miss! Atualizado apenas RAM no end {addr}")