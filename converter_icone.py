from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent

entrada = BASE_DIR / "pieces" / "tabuleiro.png"
saida = BASE_DIR / "pieces" / "tabuleiro.ico"

img = Image.open(entrada)

# Mantém transparência se existir
img = img.convert("RGBA")

# Tamanhos que o Windows utiliza
img.save(
    saida,
    format="ICO",
    sizes=[
        (8, 8),
        (16, 16),
        (24, 24),
        (32, 32),
        (48, 48),
        (64, 64),
        (128, 128),
        (256, 256),
    ],
)

print(f"Ícone criado com sucesso:\n{saida}")
