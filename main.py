import sys
from pathlib import Path

import chess

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QInputDialog,
    QPushButton,
    QWidget,
)


# Funciona tanto no Python quanto no executável criado pelo PyInstaller.
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

PIECES_DIR = BASE_DIR / "pieces"

BOARD_SIZE = 800
CONTROL_HEIGHT = 50
WINDOW_HEIGHT = BOARD_SIZE + CONTROL_HEIGHT
SQUARE_SIZE = BOARD_SIZE // 8


PIECE_FILES = {
    "P": "white_pawn.svg",
    "N": "white_knight.svg",
    "B": "white_bishop.svg",
    "R": "white_rook.svg",
    "Q": "white_queen.svg",
    "K": "white_king.svg",
    "p": "black_pawn.svg",
    "n": "black_knight.svg",
    "b": "black_bishop.svg",
    "r": "black_rook.svg",
    "q": "black_queen.svg",
    "k": "black_king.svg",
}


class Tabuleiro(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Tabuleiro de Xadrez")
        self.setFixedSize(BOARD_SIZE, WINDOW_HEIGHT)

        self.board = chess.Board()

        self.casa_selecionada = None
        self.destinos_legais = []
        self.ultimo_movimento = None

        self.tabuleiro_invertido = False

        # Controle do arraste.
        self.arrastando = False
        self.origem_arraste = None
        self.posicao_mouse = QPointF()
        self.posicao_inicial_mouse = QPointF()
        self.movimento_mouse_ocorreu = False

        # Cores definitivas do tabuleiro.
        self.cor_clara = QColor(255, 255, 221)
        self.cor_escura = QColor(134, 166, 102)

        self.svg_renderers = {}

        self.carregar_pecas()
        self.criar_controles()

    def carregar_pecas(self):
        for simbolo, nome_arquivo in PIECE_FILES.items():
            caminho = PIECES_DIR / nome_arquivo

            if not caminho.exists():
                raise FileNotFoundError(
                    f"Arquivo não encontrado: {caminho}"
                )

            renderer = QSvgRenderer(str(caminho))

            if not renderer.isValid():
                raise RuntimeError(
                    f"SVG inválido ou não carregado: {caminho}"
                )

            self.svg_renderers[simbolo] = renderer

    def criar_controles(self):
        self.botao_inverter = QPushButton(
            "Inverter tabuleiro",
            self,
        )

        self.botao_inverter.setGeometry(
            10,
            BOARD_SIZE + 7,
            180,
            36,
        )

        self.botao_inverter.clicked.connect(
            self.inverter_tabuleiro
        )

    def inverter_tabuleiro(self):
        self.tabuleiro_invertido = not self.tabuleiro_invertido

        self.arrastando = False
        self.origem_arraste = None
        self.movimento_mouse_ocorreu = False
        self.limpar_selecao()

        if self.tabuleiro_invertido:
            self.botao_inverter.setText("Visão das brancas")
        else:
            self.botao_inverter.setText("Visão das pretas")

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        self.desenhar_casas(painter)
        self.destacar_ultima_jogada(painter)
        self.destacar_selecao(painter)
        self.desenhar_destinos_legais(painter)
        self.desenhar_pecas(painter)
        self.desenhar_peca_arrastada(painter)

    def desenhar_casas(self, painter):
        for linha in range(8):
            for coluna in range(8):
                cor = (
                    self.cor_clara
                    if (linha + coluna) % 2 == 0
                    else self.cor_escura
                )

                x = coluna * SQUARE_SIZE
                y = linha * SQUARE_SIZE

                painter.fillRect(
                    x,
                    y,
                    SQUARE_SIZE,
                    SQUARE_SIZE,
                    cor,
                )

    def desenhar_pecas(self, painter):
        margem = 8

        for square in chess.SQUARES:
            if self.arrastando and square == self.origem_arraste:
                continue

            piece = self.board.piece_at(square)

            if piece is None:
                continue

            renderer = self.svg_renderers[piece.symbol()]

            coluna, linha = self.casa_para_tela(square)

            x = coluna * SQUARE_SIZE
            y = linha * SQUARE_SIZE

            area = QRectF(
                x + margem,
                y + margem,
                SQUARE_SIZE - margem * 2,
                SQUARE_SIZE - margem * 2,
            )

            renderer.render(painter, area)

    def desenhar_peca_arrastada(self, painter):
        if not self.arrastando or self.origem_arraste is None:
            return

        piece = self.board.piece_at(self.origem_arraste)

        if piece is None:
            return

        renderer = self.svg_renderers[piece.symbol()]

        tamanho = SQUARE_SIZE - 10

        x = self.posicao_mouse.x() - tamanho / 2
        y = self.posicao_mouse.y() - tamanho / 2

        area = QRectF(
            x,
            y,
            tamanho,
            tamanho,
        )

        renderer.render(painter, area)

    def destacar_selecao(self, painter):
        if self.casa_selecionada is None:
            return

        coluna, linha = self.casa_para_tela(
            self.casa_selecionada
        )

        x = coluna * SQUARE_SIZE
        y = linha * SQUARE_SIZE

        painter.fillRect(
            x,
            y,
            SQUARE_SIZE,
            SQUARE_SIZE,
            QColor(255, 255, 0, 90),
        )

        painter.setPen(
            QPen(
                QColor(255, 215, 0),
                4,
            )
        )

        painter.setBrush(Qt.NoBrush)

        painter.drawRect(
            x + 2,
            y + 2,
            SQUARE_SIZE - 4,
            SQUARE_SIZE - 4,
        )

    def desenhar_destinos_legais(self, painter):
        for destino in self.destinos_legais:
            coluna, linha = self.casa_para_tela(destino)

            x = coluna * SQUARE_SIZE
            y = linha * SQUARE_SIZE

            existe_peca = self.board.piece_at(destino)

            if existe_peca is not None:
                painter.setPen(
                    QPen(
                        QColor(20, 20, 20, 130),
                        7,
                    )
                )

                painter.setBrush(Qt.NoBrush)

                painter.drawEllipse(
                    x + 8,
                    y + 8,
                    SQUARE_SIZE - 16,
                    SQUARE_SIZE - 16,
                )
            else:
                painter.setPen(Qt.NoPen)
                painter.setBrush(
                    QColor(20, 20, 20, 110)
                )

                tamanho = SQUARE_SIZE // 4

                painter.drawEllipse(
                    x + (SQUARE_SIZE - tamanho) // 2,
                    y + (SQUARE_SIZE - tamanho) // 2,
                    tamanho,
                    tamanho,
                )

    def destacar_ultima_jogada(self, painter):
        if self.ultimo_movimento is None:
            return

        casas = [
            self.ultimo_movimento.from_square,
            self.ultimo_movimento.to_square,
        ]

        for square in casas:
            coluna, linha = self.casa_para_tela(square)

            x = coluna * SQUARE_SIZE
            y = linha * SQUARE_SIZE

            painter.fillRect(
                x,
                y,
                SQUARE_SIZE,
                SQUARE_SIZE,
                QColor(120, 180, 70, 100),
            )

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        square = self.posicao_para_casa(event.position())

        if square is None:
            return

        piece = self.board.piece_at(square)

        self.posicao_inicial_mouse = event.position()
        self.posicao_mouse = event.position()
        self.movimento_mouse_ocorreu = False

        if (
            piece is not None
            and piece.color == self.board.turn
        ):
            self.arrastando = True
            self.origem_arraste = square
            self.selecionar_casa(square)

        self.update()

    def mouseMoveEvent(self, event):
        if not self.arrastando:
            return

        self.posicao_mouse = event.position()

        distancia = (
            self.posicao_mouse - self.posicao_inicial_mouse
        ).manhattanLength()

        if distancia > 5:
            self.movimento_mouse_ocorreu = True

        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        destino = self.posicao_para_casa(event.position())

        origem = self.origem_arraste
        houve_arraste = self.movimento_mouse_ocorreu

        self.arrastando = False
        self.origem_arraste = None
        self.movimento_mouse_ocorreu = False

        if origem is None:
            self.update()
            return

        if destino is None:
            self.limpar_selecao()
            self.update()
            return

        if houve_arraste:
            self.casa_selecionada = origem
            self.tentar_movimento(destino)
        else:
            if destino == origem:
                self.selecionar_casa(origem)
            elif self.casa_selecionada is not None:
                self.tentar_movimento(destino)

        self.update()

    def selecionar_casa(self, square):
        piece = self.board.piece_at(square)

        if piece is None:
            self.limpar_selecao()
            return

        if piece.color != self.board.turn:
            self.limpar_selecao()
            return

        self.casa_selecionada = square

        self.destinos_legais = [
            movimento.to_square
            for movimento in self.board.legal_moves
            if movimento.from_square == square
        ]

    def escolher_promocao(self):
        opcoes = [
            "Dama",
            "Torre",
            "Bispo",
            "Cavalo",
        ]

        escolha, confirmado = QInputDialog.getItem(
            self,
            "Promoção do peão",
            "Escolha a nova peça:",
            opcoes,
            0,
            False,
        )

        if not confirmado:
            return None

        promocoes = {
            "Dama": chess.QUEEN,
            "Torre": chess.ROOK,
            "Bispo": chess.BISHOP,
            "Cavalo": chess.KNIGHT,
        }

        return promocoes[escolha]

    def tentar_movimento(self, destino):
        origem = self.casa_selecionada

        if origem is None:
            return

        piece_destino = self.board.piece_at(destino)

        if (
            piece_destino is not None
            and piece_destino.color == self.board.turn
        ):
            self.selecionar_casa(destino)
            return

        piece_origem = self.board.piece_at(origem)

        if piece_origem is None:
            self.limpar_selecao()
            return

        movimento = chess.Move(origem, destino)

        if (
            piece_origem.piece_type == chess.PAWN
            and chess.square_rank(destino) in (0, 7)
        ):
            promocao = self.escolher_promocao()

            if promocao is None:
                return

            movimento = chess.Move(
                origem,
                destino,
                promotion=promocao,
            )

        if movimento in self.board.legal_moves:
            self.board.push(movimento)
            self.ultimo_movimento = movimento

            print(
                f"Movimento: {movimento.uci()} | "
                f"FEN: {self.board.fen()}"
            )

        self.limpar_selecao()

    def limpar_selecao(self):
        self.casa_selecionada = None
        self.destinos_legais = []

    def posicao_para_casa(self, posicao):
        if posicao.y() >= BOARD_SIZE:
            return None

        coluna = int(posicao.x() // SQUARE_SIZE)
        linha = int(posicao.y() // SQUARE_SIZE)

        if not 0 <= coluna < 8 or not 0 <= linha < 8:
            return None

        return self.tela_para_casa(coluna, linha)

    def casa_para_tela(self, square):
        coluna = chess.square_file(square)
        rank = chess.square_rank(square)

        if self.tabuleiro_invertido:
            coluna_tela = 7 - coluna
            linha_tela = rank
        else:
            coluna_tela = coluna
            linha_tela = 7 - rank

        return coluna_tela, linha_tela

    def tela_para_casa(self, coluna, linha):
        if self.tabuleiro_invertido:
            arquivo = 7 - coluna
            rank = linha
        else:
            arquivo = coluna
            rank = 7 - linha

        return chess.square(
            arquivo,
            rank,
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)

    janela = Tabuleiro()
    janela.show()

    sys.exit(app.exec())