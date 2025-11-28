# config.py

# --- Configurações de Arquitetura ---
WORD_SIZE = 16          # Tamanho da palavra (bits)
ADDR_SIZE = 12          # Tamanho do endereço (bits) - para 4096 palavras
MEMORY_SIZE = 4096      # Quantidade de palavras na RAM
CACHE_SIZE = 16         # Quantidade de linhas na Cache (exemplo)
BLOCK_SIZE = 4          # Palavras por bloco (para a Cache)

# --- Máscaras de Bits (Essencial para simular 16 bits em Python) ---
MASK_16BIT = 0xFFFF     # 1111 1111 1111 1111
MASK_12BIT = 0x0FFF     # 0000 1111 1111 1111

# --- Configurações de Interface (GUI) ---
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
COLOR_BG = "#f0f0f0"
COLOR_COMPONENT = "white"
COLOR_HIGHLIGHT = "#ff5555" # Cor quando ativa (vermelho claro)
COLOR_BUS_ACTIVE = "red"
SPEED_DELAY = 0.5       # Segundos entre subciclos