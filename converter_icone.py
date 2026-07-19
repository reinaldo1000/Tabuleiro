from pathlib import Path
from PIL import Image, ImageOps

BASE_DIR = Path(__file__).resolve().parent

entrada = BASE_DIR / "pieces" / "tabuleiro.png"
saida = BASE_DIR / "pieces" / "tabuleiro.ico"

if not entrada.exists():
    raise FileNotFoundError(f"Imagem não encontrada: {entrada}")

imagem = Image.open(entrada).convert("RGBA")

# Recorta a imagem para ficar quadrada sem deformar.
lado = min(imagem.width, imagem.height)

esquerda = (imagem.width - lado) // 2
topo = (imagem.height - lado) // 2

imagem = imagem.crop(
    (
        esquerda,
        topo,
        esquerda + lado,
        topo + lado,
    )
)

# Cria uma imagem quadrada de alta qualidade.
imagem = ImageOps.fit(
    imagem,
    (256, 256),
    method=Image.Resampling.LANCZOS,
)

tamanhos = [
    (16, 16),
    (24, 24),
    (32, 32),
    (40, 40),
    (48, 48),
    (64, 64),
    (96, 96),
    (128, 128),
    (256, 256),
]

imagem.save(
    saida,
    format="ICO",
    sizes=tamanhos,
)

print("Ícone criado com sucesso:")
print(saida)