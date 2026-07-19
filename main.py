import sys
from pathlib import Path

import chess

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


# ============================================================
# CAMINHOS
# ============================================================

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

PIECES_DIR = BASE_DIR / "pieces"
PIECES2_DIR = BASE_DIR / "pieces2"


# ============================================================
# ARQUIVOS DAS PEÇAS
# ============================================================

PECAS_ESTILO_1 = {
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

PECAS_ESTILO_2 = {
    "P": "wp.png",
    "N": "wn.png",
    "B": "wb.png",
    "R": "wr.png",
    "Q": "wq.png",
    "K": "wk.png",
    "p": "bp.png",
    "n": "bn.png",
    "b": "bb.png",
    "r": "br.png",
    "q": "bq.png",
    "k": "bk.png",
}


# ============================================================
# JANELA DE PROMOÇÃO
# ============================================================

class DialogoPromocao(QDialog):

    def __init__(self, cor_branca: bool, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Promoção")
        self.setModal(True)
        self.peca_escolhida = chess.QUEEN

        layout = QVBoxLayout(self)

        texto = QLabel("Escolha a peça para promoção:")
        layout.addWidget(texto)

        nomes = [
            ("Dama", chess.QUEEN),
            ("Torre", chess.ROOK),
            ("Bispo", chess.BISHOP),
            ("Cavalo", chess.KNIGHT),
        ]

        for nome, tipo_peca in nomes:
            botao = QPushButton(nome)
            botao.clicked.connect(
                lambda marcado=False, peca=tipo_peca: self.escolher(peca)
            )
            layout.addWidget(botao)

        self.resize(250, 220)

    def escolher(self, tipo_peca):
        self.peca_escolhida = tipo_peca
        self.accept()


# ============================================================
# WIDGET DO TABULEIRO
# ============================================================

class TabuleiroWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.board = chess.Board()

        self.tabuleiro_invertido = False
        self.estilo_visual = 1

        self.casa_selecionada = None
        self.ultimo_movimento = None

        self.arrastando = False
        self.origem_arrasto = None
        self.posicao_mouse = QPoint()
        self.posicao_clique = QPoint()

        self.tamanho_tabuleiro = 800
        self.setFixedSize(
            self.tamanho_tabuleiro,
            self.tamanho_tabuleiro,
        )

        self.setMouseTracking(True)

        self.svg_renderers = {}
        self.pixmaps_estilo_2 = {}

        self.carregar_pecas()

        self.imagem_tabuleiro_2 = QPixmap(
            str(PIECES2_DIR / "tabuleiro.png")
        )

    # ========================================================
    # CARREGAMENTO DAS IMAGENS
    # ========================================================

    def carregar_pecas(self):

        self.svg_renderers.clear()
        self.pixmaps_estilo_2.clear()

        for simbolo, arquivo in PECAS_ESTILO_1.items():

            caminho = PIECES_DIR / arquivo

            if caminho.exists():
                self.svg_renderers[simbolo] = QSvgRenderer(
                    str(caminho)
                )

        for simbolo, arquivo in PECAS_ESTILO_2.items():

            caminho = PIECES2_DIR / arquivo

            if caminho.exists():
                self.pixmaps_estilo_2[simbolo] = QPixmap(
                    str(caminho)
                )

    # ========================================================
    # TAMANHOS E COORDENADAS
    # ========================================================

    def tamanho_casa(self):
        return self.width() / 8

    def casa_para_tela(self, square):

        arquivo = chess.square_file(square)
        linha = chess.square_rank(square)

        if self.tabuleiro_invertido:
            coluna_tela = 7 - arquivo
            linha_tela = linha
        else:
            coluna_tela = arquivo
            linha_tela = 7 - linha

        tamanho = self.tamanho_casa()

        x = coluna_tela * tamanho
        y = linha_tela * tamanho

        return x, y

    def tela_para_casa(self, ponto):

        tamanho = self.tamanho_casa()

        coluna_tela = int(ponto.x() / tamanho)
        linha_tela = int(ponto.y() / tamanho)

        if not 0 <= coluna_tela < 8:
            return None

        if not 0 <= linha_tela < 8:
            return None

        if self.tabuleiro_invertido:
            arquivo = 7 - coluna_tela
            linha = linha_tela
        else:
            arquivo = coluna_tela
            linha = 7 - linha_tela

        return chess.square(arquivo, linha)

    # ========================================================
    # DESENHO
    # ========================================================

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        self.desenhar_tabuleiro(painter)
        self.desenhar_ultimo_movimento(painter)
        self.desenhar_casa_selecionada(painter)
        self.desenhar_movimentos_legais(painter)
        self.desenhar_pecas(painter)
        self.desenhar_peca_arrastada(painter)
        self.desenhar_coordenadas(painter)

    def desenhar_tabuleiro(self, painter):

        if (
            self.estilo_visual == 2
            and not self.imagem_tabuleiro_2.isNull()
        ):
            painter.drawPixmap(
                self.rect(),
                self.imagem_tabuleiro_2,
            )
            return

        cor_clara = QColor(255, 255, 221)
        cor_escura = QColor(134, 166, 102)

        tamanho = self.tamanho_casa()

        for linha in range(8):
            for coluna in range(8):

                cor = (
                    cor_clara
                    if (linha + coluna) % 2 == 0
                    else cor_escura
                )

                painter.fillRect(
                    QRectF(
                        coluna * tamanho,
                        linha * tamanho,
                        tamanho,
                        tamanho,
                    ),
                    cor,
                )

    def desenhar_ultimo_movimento(self, painter):

        if self.ultimo_movimento is None:
            return

        cor = QColor(255, 230, 0, 100)
        tamanho = self.tamanho_casa()

        for square in [
            self.ultimo_movimento.from_square,
            self.ultimo_movimento.to_square,
        ]:
            x, y = self.casa_para_tela(square)

            painter.fillRect(
                QRectF(x, y, tamanho, tamanho),
                cor,
            )

    def desenhar_casa_selecionada(self, painter):

        if self.casa_selecionada is None:
            return

        x, y = self.casa_para_tela(
            self.casa_selecionada
        )

        tamanho = self.tamanho_casa()

        painter.fillRect(
            QRectF(x, y, tamanho, tamanho),
            QColor(255, 255, 0, 100),
        )

        caneta = QPen(QColor(255, 215, 0))
        caneta.setWidth(4)

        painter.setPen(caneta)
        painter.drawRect(
            QRectF(
                x + 2,
                y + 2,
                tamanho - 4,
                tamanho - 4,
            )
        )

    def desenhar_movimentos_legais(self, painter):

        if self.casa_selecionada is None:
            return

        tamanho = self.tamanho_casa()

        movimentos = [
            movimento
            for movimento in self.board.legal_moves
            if movimento.from_square == self.casa_selecionada
        ]

        painter.setPen(Qt.NoPen)

        for movimento in movimentos:

            x, y = self.casa_para_tela(
                movimento.to_square
            )

            destino_ocupado = (
                self.board.piece_at(
                    movimento.to_square
                )
                is not None
            )

            if destino_ocupado:

                caneta = QPen(
                    QColor(40, 40, 40, 140)
                )
                caneta.setWidth(7)

                painter.setPen(caneta)
                painter.setBrush(Qt.NoBrush)

                painter.drawEllipse(
                    QRectF(
                        x + 8,
                        y + 8,
                        tamanho - 16,
                        tamanho - 16,
                    )
                )

                painter.setPen(Qt.NoPen)

            else:

                painter.setBrush(
                    QColor(40, 40, 40, 120)
                )

                raio = tamanho * 0.14

                painter.drawEllipse(
                    QRectF(
                        x + tamanho / 2 - raio,
                        y + tamanho / 2 - raio,
                        raio * 2,
                        raio * 2,
                    )
                )

    def desenhar_pecas(self, painter):

        tamanho = self.tamanho_casa()

        for square, piece in self.board.piece_map().items():

            if (
                self.arrastando
                and square == self.origem_arrasto
            ):
                continue

            simbolo = piece.symbol()

            x, y = self.casa_para_tela(square)

            margem = tamanho * 0.06

            retangulo = QRectF(
                x + margem,
                y + margem,
                tamanho - margem * 2,
                tamanho - margem * 2,
            )

            self.desenhar_uma_peca(
                painter,
                simbolo,
                retangulo,
            )

    def desenhar_uma_peca(
        self,
        painter,
        simbolo,
        retangulo,
    ):

        if self.estilo_visual == 1:

            renderer = self.svg_renderers.get(simbolo)

            if renderer is not None:
                renderer.render(
                    painter,
                    retangulo,
                )

        else:

            pixmap = self.pixmaps_estilo_2.get(
                simbolo
            )

            if pixmap is not None and not pixmap.isNull():

                painter.drawPixmap(
                    retangulo.toRect(),
                    pixmap,
                )

    def desenhar_peca_arrastada(self, painter):

        if not self.arrastando:
            return

        if self.origem_arrasto is None:
            return

        piece = self.board.piece_at(
            self.origem_arrasto
        )

        if piece is None:
            return

        tamanho = self.tamanho_casa()

        retangulo = QRectF(
            self.posicao_mouse.x() - tamanho / 2,
            self.posicao_mouse.y() - tamanho / 2,
            tamanho,
            tamanho,
        )

        painter.setOpacity(0.85)

        self.desenhar_uma_peca(
            painter,
            piece.symbol(),
            retangulo,
        )

        painter.setOpacity(1.0)

    def desenhar_coordenadas(self, painter):

        tamanho = self.tamanho_casa()

        painter.setPen(QColor(30, 30, 30, 190))

        fonte = painter.font()
        fonte.setBold(True)
        fonte.setPointSize(9)
        painter.setFont(fonte)

        for coluna in range(8):

            if self.tabuleiro_invertido:
                letra = chr(ord("h") - coluna)
            else:
                letra = chr(ord("a") + coluna)

            painter.drawText(
                int(coluna * tamanho + 5),
                int(self.height() - 6),
                letra,
            )

        for linha in range(8):

            if self.tabuleiro_invertido:
                numero = str(linha + 1)
            else:
                numero = str(8 - linha)

            painter.drawText(
                int(self.width() - 14),
                int(linha * tamanho + 15),
                numero,
            )

    # ========================================================
    # CLIQUES E ARRASTE
    # ========================================================

    def mousePressEvent(self, event: QMouseEvent):

        if event.button() != Qt.LeftButton:
            return

        square = self.tela_para_casa(
            event.position().toPoint()
        )

        if square is None:
            return

        self.posicao_clique = event.position().toPoint()
        self.posicao_mouse = event.position().toPoint()

        piece = self.board.piece_at(square)

        if (
            piece is not None
            and piece.color == self.board.turn
        ):
            self.origem_arrasto = square
        else:
            self.origem_arrasto = None

        self.arrastando = False

    def mouseMoveEvent(self, event: QMouseEvent):

        self.posicao_mouse = event.position().toPoint()

        if self.origem_arrasto is None:
            return

        distancia = (
            self.posicao_mouse
            - self.posicao_clique
        ).manhattanLength()

        if distancia > 8:
            self.arrastando = True
            self.casa_selecionada = (
                self.origem_arrasto
            )
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):

        if event.button() != Qt.LeftButton:
            return

        square_destino = self.tela_para_casa(
            event.position().toPoint()
        )

        if self.arrastando:

            origem = self.origem_arrasto

            self.arrastando = False
            self.origem_arrasto = None

            if (
                origem is not None
                and square_destino is not None
            ):
                self.tentar_movimento(
                    origem,
                    square_destino,
                )

            self.update()
            return

        self.origem_arrasto = None

        if square_destino is not None:
            self.processar_clique(
                square_destino
            )

        self.update()

    def processar_clique(self, square):

        piece = self.board.piece_at(square)

        if self.casa_selecionada is None:

            if (
                piece is not None
                and piece.color == self.board.turn
            ):
                self.casa_selecionada = square

            return

        if square == self.casa_selecionada:
            self.casa_selecionada = None
            return

        if (
            piece is not None
            and piece.color == self.board.turn
        ):
            self.casa_selecionada = square
            return

        origem = self.casa_selecionada

        if self.tentar_movimento(origem, square):
            self.casa_selecionada = None

    # ========================================================
    # MOVIMENTOS
    # ========================================================

    def tentar_movimento(
        self,
        origem,
        destino,
    ):

        piece = self.board.piece_at(origem)

        if piece is None:
            return False

        promocao = None

        if piece.piece_type == chess.PAWN:

            rank_destino = chess.square_rank(destino)

            if rank_destino in [0, 7]:

                dialogo = DialogoPromocao(
                    piece.color == chess.WHITE,
                    self,
                )

                if dialogo.exec() != QDialog.Accepted:
                    return False

                promocao = dialogo.peca_escolhida

        movimento = chess.Move(
            origem,
            destino,
            promotion=promocao,
        )

        if movimento not in self.board.legal_moves:
            return False

        self.board.push(movimento)

        self.ultimo_movimento = movimento
        self.casa_selecionada = None

        self.update()

        return True

    # ========================================================
    # CONTROLES
    # ========================================================

    def inverter_tabuleiro(self):

        self.tabuleiro_invertido = (
            not self.tabuleiro_invertido
        )

        self.update()

    def trocar_visual(self):

        if self.estilo_visual == 1:
            self.estilo_visual = 2
        else:
            self.estilo_visual = 1

        self.update()

    def nova_partida(self):

        self.board.reset()

        self.casa_selecionada = None
        self.ultimo_movimento = None
        self.arrastando = False
        self.origem_arrasto = None

        self.update()

    def desfazer_movimento(self):

        if not self.board.move_stack:
            return

        self.board.pop()

        if self.board.move_stack:
            self.ultimo_movimento = (
                self.board.peek()
            )
        else:
            self.ultimo_movimento = None

        self.casa_selecionada = None
        self.update()


# ============================================================
# JANELA PRINCIPAL
# ============================================================

class JanelaPrincipal(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Tabuleiro de Xadrez")

        caminho_icone = PIECES_DIR / "tabuleiro.ico"

        if caminho_icone.exists():
            self.setWindowIcon(
                QIcon(str(caminho_icone))
            )

        widget_central = QWidget()
        self.setCentralWidget(widget_central)

        layout_principal = QVBoxLayout(
            widget_central
        )

        self.tabuleiro = TabuleiroWidget()

        layout_principal.addWidget(
            self.tabuleiro,
            alignment=Qt.AlignCenter,
        )

        layout_botoes = QHBoxLayout()

        self.botao_inverter = QPushButton(
            "Inverter tabuleiro"
        )

        self.botao_visual = QPushButton(
            "Trocar visual"
        )

        self.botao_desfazer = QPushButton(
            "Desfazer"
        )

        self.botao_nova = QPushButton(
            "Nova partida"
        )

        self.botao_inverter.clicked.connect(
            self.tabuleiro.inverter_tabuleiro
        )

        self.botao_visual.clicked.connect(
            self.trocar_visual
        )

        self.botao_desfazer.clicked.connect(
            self.tabuleiro.desfazer_movimento
        )

        self.botao_nova.clicked.connect(
            self.tabuleiro.nova_partida
        )

        layout_botoes.addWidget(
            self.botao_inverter
        )

        layout_botoes.addWidget(
            self.botao_visual
        )

        layout_botoes.addWidget(
            self.botao_desfazer
        )

        layout_botoes.addWidget(
            self.botao_nova
        )

        layout_principal.addLayout(
            layout_botoes
        )

        self.label_visual = QLabel(
            "Visual atual: peças clássicas"
        )

        self.label_visual.setAlignment(
            Qt.AlignCenter
        )

        layout_principal.addWidget(
            self.label_visual
        )

        self.setFixedSize(840, 910)

    def trocar_visual(self):

        self.tabuleiro.trocar_visual()

        if self.tabuleiro.estilo_visual == 1:
            self.label_visual.setText(
                "Visual atual: peças clássicas"
            )
        else:
            self.label_visual.setText(
                "Visual atual: peças alternativas"
            )


# ============================================================
# INÍCIO DO PROGRAMA
# ============================================================

def main():

    app = QApplication(sys.argv)

    caminho_icone = PIECES_DIR / "tabuleiro.ico"

    if caminho_icone.exists():
        app.setWindowIcon(
            QIcon(str(caminho_icone))
        )

    janela = JanelaPrincipal()
    janela.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()