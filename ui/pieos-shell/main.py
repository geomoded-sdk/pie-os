#!/usr/bin/env python3
#=============================================================================
# Pie OS Shell - Interface Console estilo Xbox 360
# PyQt5 - UI otimizada para TV/Gamepad com tema verde claro
#=============================================================================

import sys, os, subprocess, glob, threading, signal, math
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import (Qt, QTimer, QRect, QPropertyAnimation,
    QEasingCurve, pyqtSignal, QPoint, QParallelAnimationGroup,
    QAnimationGroup, QAbstractAnimation, QSize)
from PyQt5.QtGui import (QFont, QColor, QPainter, QBrush, QLinearGradient,
    QPixmap, QFontDatabase, QRadialGradient, QPen, QPainterPath, QImage,
    QPolygonF, QConicalGradient)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QStackedWidget, QGridLayout,
    QScrollArea, QFrame, QListWidget, QListWidgetItem, QSlider,
    QMessageBox, QDialog, QGraphicsDropShadowEffect, QSizePolicy,
    QSpacerItem, QProgressBar)

#=============================================================================
# TEMA - Xbox 360 inspirado, verde claro com mínimo de azul
#=============================================================================

C = {
    "bg":           "#1a1a1a",
    "bg_card":      "#222222",
    "bg_blade":     "#2a2a2a",
    "accent":       "#A8D854",
    "accent_dark":  "#7AB832",
    "accent_glow":  "#C8F066",
    "text":         "#FFFFFF",
    "text_dim":     "#999999",
    "text_muted":   "#666666",
    "border":       "#333333",
    "border_focus": "#A8D854",
    "blade_inactive":"#3a3a3a",
    "blade_hover":  "#4a4a4a",
    "success":      "#A8D854",
    "danger":       "#E74C3C",
    "warning":      "#F39C12",
}

def hex(qcolor, alpha=255):
    c = QColor(qcolor)
    c.setAlpha(alpha)
    return c

def shadow(radius=12, color="#000000", alpha=80, offset=0):
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(radius)
    s.setColor(QColor(0,0,0,alpha))
    s.setOffset(offset, offset)
    return s

def gradient_bg(w, h, c1="#1a1a1a", c2="#222222"):
    g = QLinearGradient(0, 0, 0, h)
    g.setColorAt(0, hex(c1))
    g.setColorAt(1, hex(c2))
    return g

#=============================================================================
# WIDGETS PERSONALIZADOS
#=============================================================================

class BladePanel(QWidget):
    """Barra de navegação estilo Xbox 360 blades"""
    bladeChanged = pyqtSignal(int)

    def __init__(self, blades, parent=None):
        super().__init__(parent)
        self.blades = blades
        self.current = 0
        self.hovered = -1
        self.anim_progress = 0.0
        self.setFixedHeight(85)
        self.setMouseTracking(True)
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick_anim)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        p.fillRect(self.rect(), hex(C["bg_blade"]))
        line = QPen(hex(C["border"], 60), 1)
        p.setPen(line)
        p.drawLine(0, h-1, w, h-1)

        blade_w = 180
        total = len(self.blades) * blade_w
        start_x = (w - total) // 2
        blade_h = 50
        blade_y = (h - blade_h) // 2 - 2
        radius = 10

        for i, blade in enumerate(self.blades):
            bx = start_x + i * blade_w
            by = blade_y
            is_active = (i == self.current)
            is_hovered = (i == self.hovered)

            path = QPainterPath()
            path.addRoundedRect(bx, by, blade_w-8, blade_h, radius, radius)

            if is_active:
                grad = QLinearGradient(bx, by, bx, by + blade_h)
                grad.setColorAt(0, hex(C["accent_glow"]))
                grad.setColorAt(0.5, hex(C["accent"]))
                grad.setColorAt(1, hex(C["accent_dark"]))
                p.fillPath(path, QBrush(grad))

                bar = QPainterPath()
                bar.addRoundedRect(bx+4, by+blade_h-3, blade_w-16, 3, 2, 2)
                p.fillPath(bar, hex(C["text"], 200))

                p.setPen(QPen(QColor(255,255,255,60), 1))
                glow = QPainterPath()
                glow.addRoundedRect(bx+2, by+2, blade_w-12, blade_h//2, 8, 8)
                p.fillPath(glow, QColor(255,255,255,30))

            elif is_hovered:
                p.fillPath(path, hex(C["blade_hover"]))
                p.setPen(QPen(hex(C["accent"], 100), 2))
                p.drawPath(path)
            else:
                p.fillPath(path, hex(C["blade_inactive"]))

            p.setPen(Qt.NoPen)
            if is_active:
                p.setPen(hex(C["bg"]))
            else:
                p.setPen(hex(C["text_dim"] if not is_hovered else C["text"]))
            font = QFont("Segoe UI", 14 if is_active else 13,
                        QFont.Bold if is_active else QFont.Normal)
            p.setFont(font)
            p.drawText(QRect(bx, by, blade_w-8, blade_h),
                      Qt.AlignCenter, blade)

    def mouseMoveEvent(self, e):
        blade_w = 180
        total = len(self.blades) * blade_w
        start_x = (self.width() - total) // 2
        blade_h = 50
        blade_y = (self.height() - blade_h) // 2 - 2
        idx = (e.x() - start_x) // blade_w
        if 0 <= idx < len(self.blades):
            bx = start_x + idx * blade_w
            if bx <= e.x() <= bx + blade_w-8 and blade_y <= e.y() <= blade_y + blade_h:
                self.hovered = idx
                self.update()
                return
        self.hovered = -1
        self.update()

    def leaveEvent(self, e):
        self.hovered = -1
        self.update()

    def mousePressEvent(self, e):
        blade_w = 180
        total = len(self.blades) * blade_w
        start_x = (self.width() - total) // 2
        blade_h = 50
        blade_y = (self.height() - blade_h) // 2 - 2
        idx = (e.x() - start_x) // blade_w
        if 0 <= idx < len(self.blades):
            bx = start_x + idx * blade_w
            if bx <= e.x() <= bx + blade_w-8 and blade_y <= e.y() <= blade_y + blade_h:
                self.set_blade(idx)

    def set_blade(self, idx):
        if idx != self.current:
            self.current = idx
            self.bladeChanged.emit(idx)
            self.update()

    def _tick_anim(self):
        pass


class GameCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, title, path, parent=None):
        super().__init__(parent)
        self.title = title
        self.path = path
        self._hover = False
        self.setFixedSize(220, 280)
        self.setCursor(Qt.PointingHandCursor)
        self.setGraphicsEffect(shadow(15, "#000000", 100, 2))
        self._setup()

    def _setup(self):
        self.setStyleSheet(f"""
            GameCard {{
                background: {C["bg_card"]};
                border: 2px solid {C["border"]};
                border-radius: 18px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        icon = QFrame()
        icon.setFixedSize(196, 170)
        icon.setStyleSheet(f"""
            QFrame {{
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.8,
                    stop:0 {C["bg"]}, stop:1 {C["border"]});
                border-radius: 14px;
                border: 1px solid {C["border"]};
            }}
        """)
        il = QVBoxLayout(icon)
        emoji = QLabel(self._emoji())
        emoji.setAlignment(Qt.AlignCenter)
        emoji.setStyleSheet("font-size: 52px; background: transparent;")
        il.addWidget(emoji)
        layout.addWidget(icon)

        lbl = QLabel(self.title)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"""
            QLabel {{
                color: {C["text"]}; font-size: 13px; font-weight: bold;
                background: transparent; padding: 2px;
            }}
        """)
        layout.addWidget(lbl)

        tag = QLabel(self._tag())
        tag.setAlignment(Qt.AlignCenter)
        tag.setStyleSheet(f"""
            QLabel {{
                color: {C["accent"]}; font-size: 10px;
                background: transparent; letter-spacing: 1px;
            }}
        """)
        layout.addWidget(tag)

    def _emoji(self):
        ext = Path(self.path).suffix.lower()
        return {"": "📦", ".appimage": "📦", ".xex": "🎮", ".sh": "⚡"}.get(ext, "🎮")

    def _tag(self):
        ext = Path(self.path).suffix.lower()
        tags = {".appimage": "APPIMAGE", ".xex": "XBOX 360", ".sh": "SCRIPT"}
        return tags.get(ext, "JOGO")

    def enterEvent(self, e):
        self._hover = True
        self.setStyleSheet(f"""
            GameCard {{
                background: {C["bg_card"]};
                border: 2px solid {C["accent"]};
                border-radius: 18px;
            }}
        """)

    def leaveEvent(self, e):
        self._hover = False
        self.setStyleSheet(f"""
            GameCard {{
                background: {C["bg_card"]};
                border: 2px solid {C["border"]};
                border-radius: 18px;
            }}
        """)

    def mousePressEvent(self, e):
        self.clicked.emit(self.path)


class GlowButton(QPushButton):
    def __init__(self, text, color=C["accent"], parent=None):
        super().__init__(text, parent)
        self._color = color
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(42)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {color}; color: {C["bg"]};
                border: none; border-radius: 10px;
                padding: 8px 24px; font-size: 13px; font-weight: bold;
            }}
            QPushButton:hover {{
                background: {C["accent_glow"]};
            }}
            QPushButton:pressed {{
                background: {C["accent_dark"]};
            }}
        """)


class StatCard(QFrame):
    def __init__(self, icon, title, value, parent=None):
        super().__init__(parent)
        self.setFixedSize(260, 100)
        self.setStyleSheet(f"""
            StatCard {{
                background: {C["bg_card"]};
                border: 1px solid {C["border"]};
                border-radius: 14px;
            }}
        """)
        self.setGraphicsEffect(shadow(10, "#000000", 80, 2))
        l = QHBoxLayout(self)
        l.setContentsMargins(16, 12, 16, 12)
        ic = QLabel(icon)
        ic.setStyleSheet("font-size: 32px; background: transparent;")
        l.addWidget(ic)
        v = QVBoxLayout()
        v.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet(f"color: {C['text_dim']}; font-size: 11px; background: transparent;")
        v.addWidget(t)
        vl = QLabel(value)
        vl.setStyleSheet(f"color: {C['text']}; font-size: 18px; font-weight: bold; background: transparent;")
        v.addWidget(vl)
        l.addLayout(v)
        l.addStretch()


class SmoothStack(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._animating = False

    def slide_to(self, index):
        if index == self.currentIndex() or self._animating:
            return
        self._animating = True
        self.setCurrentIndex(index)
        QTimer.singleShot(200, lambda: setattr(self, '_animating', False))


#=============================================================================
# PÁGINAS
#=============================================================================

class HomePage(QWidget):
    launch = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup()

    def setup(self):
        l = QVBoxLayout(self)
        l.setContentsMargins(50, 25, 50, 25)
        l.setSpacing(20)

        top = QHBoxLayout()
        greet = QLabel("Olá, Jogador!")
        greet.setStyleSheet(f"color: {C['text']}; font-size: 34px; font-weight: bold;")
        top.addWidget(greet)
        top.addStretch()

        ver = QLabel(f"Pie OS • v1.0")
        ver.setStyleSheet(f"color: {C['accent']}; font-size: 13px; font-weight: bold;")
        ver.setGraphicsEffect(shadow(5, C["accent"], 60, 0))
        top.addWidget(ver)
        l.addLayout(top)

        sub = QLabel("Console System para PieBox • Todos os seus jogos em um só lugar")
        sub.setStyleSheet(f"color: {C['text_dim']}; font-size: 14px; padding-bottom: 5px;")
        l.addWidget(sub)

        cards = QHBoxLayout()
        cards.setSpacing(16)
        items = [
            ("🎮", "Jogos", "Biblioteca", "Abrir biblioteca", "accent"),
            ("📦", "AppImages", "Gerenciar", "Ver aplicativos", "accent_dark"),
            ("⚙️", "Config", "Ajustes", "Configurar sistema", "accent"),
            ("📶", "WiFi", "Redes", "Conectar", "accent_dark"),
        ]
        for ic, t, v, a, c in items:
            card = StatCard(ic, t, v)
            cards.addWidget(card)
        cards.addStretch()
        l.addLayout(cards)

        rec_label = QLabel("Jogos Recentes")
        rec_label.setStyleSheet(f"color: {C['text_dim']}; font-size: 16px; font-weight: bold; margin-top: 10px;")
        l.addWidget(rec_label)

        rec_grid = QGridLayout()
        rec_grid.setSpacing(12)
        demo_games = [
            ("Nenhum jogo encontrado", None),
        ]
        for i, (name, path) in enumerate(demo_games):
            if name == "Nenhum jogo encontrado":
                nl = QLabel("🎮  Coloque seus jogos .AppImage ou .xex em ~/Games/")
                nl.setStyleSheet(f"color: {C['text_muted']}; font-size: 14px; padding: 30px; "
                                f"background: {C['bg_card']}; border: 2px dashed {C['border']}; "
                                f"border-radius: 16px;")
                nl.setAlignment(Qt.AlignCenter)
                rec_grid.addWidget(nl, 0, 0, 1, 4)
        l.addLayout(rec_grid)
        l.addStretch()


class GamesPage(QWidget):
    launch = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.games = []
        self.setup()
        self.scan()

    def setup(self):
        l = QVBoxLayout(self)
        l.setContentsMargins(50, 25, 50, 25)
        l.setSpacing(15)

        h = QHBoxLayout()
        t = QLabel("📖  Biblioteca de Jogos")
        t.setStyleSheet(f"color: {C['text']}; font-size: 28px; font-weight: bold;")
        h.addWidget(t)
        h.addStretch()
        rf = GlowButton("🔄 Atualizar")
        rf.clicked.connect(self.scan)
        h.addWidget(rf)
        l.addLayout(h)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")

        self.grid_widget = QWidget()
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setSpacing(16)
        self.grid.setContentsMargins(0, 0, 0, 0)

        scr = QScrollArea()
        scr.setWidgetResizable(True)
        scr.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scr.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {C["bg"]}; width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {C["accent"]}; border-radius: 3px; min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        scr.setWidget(self.grid_widget)
        self.stack.addWidget(scr)

        empty = QLabel("Nenhum jogo encontrado\n\nColoque .AppImage ou .xex em:\n~/Games/  ~/Apps/")
        empty.setAlignment(Qt.AlignCenter)
        empty.setStyleSheet(f"color: {C['text_muted']}; font-size: 18px; padding: 60px;")
        self.stack.addWidget(empty)

        l.addWidget(self.stack)

    def scan(self):
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w: w.deleteLater()

        self.games = []
        row = col = 0
        dirs = [os.path.expanduser("~/Games"), os.path.expanduser("~/Apps"),
                os.path.expanduser("~/Roms"), "/mnt/games", "/mnt"]

        for d in dirs:
            if not os.path.isdir(d): continue
            for ext in ["*.AppImage", "*.appimage", "*.xex", "*.XEX", "*.sh"]:
                for fp in sorted(glob.glob(os.path.join(d, "**", ext), recursive=True)):
                    card = GameCard(Path(fp).stem, fp)
                    card.clicked.connect(self.launch.emit)
                    self.grid.addWidget(card, row, col)
                    self.games.append(fp)
                    col += 1
                    if col >= 4:
                        col = 0
                        row += 1

        self.stack.setCurrentIndex(0 if self.games else 1)


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup()

    def setup(self):
        l = QVBoxLayout(self)
        l.setContentsMargins(50, 25, 50, 25)
        l.setSpacing(10)

        t = QLabel("⚙️  Configurações")
        t.setStyleSheet(f"color: {C['text']}; font-size: 28px; font-weight: bold;")
        l.addWidget(t)

        sub = QLabel("Personalize seu PieBox")
        sub.setStyleSheet(f"color: {C['text_dim']}; font-size: 14px; padding-bottom: 10px;")
        l.addWidget(sub)

        items = [
            ("📶", "WiFi", "Conectar a redes sem fio", self._wifi),
            ("🎮", "Controles", "Gamepad USB/Wireless", self._gamepad),
            ("🖥️", "Vídeo", f"Intel HD 3000 • 720p", self._video),
            ("🔊", "Áudio", "Volume e saída", self._audio),
            ("🔄", "Sistema", "Atualizações do Pie OS", self._update),
            ("ℹ️", "Sobre", "Pie OS v1.0 • PieBox", self._about),
        ]
        for ic, ti, de, cb in items:
            l.addWidget(self._setting_row(ic, ti, de, cb))
        l.addStretch()

    def _setting_row(self, icon, title, desc, callback):
        f = QFrame()
        f.setFixedHeight(65)
        f.setStyleSheet(f"""
            QFrame {{
                background: {C["bg_card"]};
                border: 1px solid {C["border"]};
                border-radius: 12px;
            }}
            QFrame:hover {{ border: 1px solid {C["accent"]}; }}
        """)
        f.setCursor(Qt.PointingHandCursor)
        la = QHBoxLayout(f)
        la.setContentsMargins(16, 8, 16, 8)
        ic = QLabel(icon)
        ic.setStyleSheet("font-size: 24px; background: transparent;")
        ic.setFixedWidth(36)
        la.addWidget(ic)
        v = QVBoxLayout()
        v.setSpacing(1)
        ti = QLabel(title)
        ti.setStyleSheet(f"color: {C['text']}; font-size: 15px; font-weight: bold; background: transparent;")
        v.addWidget(ti)
        de = QLabel(desc)
        de.setStyleSheet(f"color: {C['text_dim']}; font-size: 11px; background: transparent;")
        v.addWidget(de)
        la.addLayout(v)
        la.addStretch()
        ar = QLabel("›")
        ar.setStyleSheet(f"color: {C['accent']}; font-size: 26px; font-weight: bold; background: transparent;")
        la.addWidget(ar)
        f.mousePressEvent = lambda e, cb=callback: cb()
        return f

    def _dialog(self, title, w=480, h=380):
        d = QDialog(self)
        d.setWindowTitle(title)
        d.setFixedSize(w, h)
        d.setStyleSheet(f"""
            QDialog {{
                background: {C["bg"]};
                border: 2px solid {C["accent"]};
                border-radius: 20px;
            }}
        """)
        la = QVBoxLayout(d)
        la.setContentsMargins(24, 20, 24, 20)
        la.setSpacing(16)
        t = QLabel(title)
        t.setStyleSheet(f"color: {C['text']}; font-size: 22px; font-weight: bold;")
        la.addWidget(t)
        return d, la

    def _wifi(self):
        d, la = self._dialog("📶  Redes WiFi")
        try:
            r = subprocess.run(["nmcli", "-t", "-f", "SSID,SIGNAL", "dev", "wifi", "list"],
                             capture_output=True, text=True, timeout=10)
            nets = r.stdout.strip().split("\n") if r.stdout.strip() else []
            if nets:
                lw = QListWidget()
                lw.setStyleSheet(f"""
                    QListWidget {{
                        background: {C["bg_card"]}; border: 1px solid {C["border"]};
                        border-radius: 10px; color: {C["text"]}; font-size: 13px;
                    }}
                    QListWidget::item {{
                        padding: 12px 16px; border-bottom: 1px solid {C["border"]};
                    }}
                    QListWidget::item:hover {{ background: {C["blade_hover"]}; }}
                """)
                for n in nets:
                    parts = n.split(":")
                    ssid = parts[0] if parts[0] else "(oculta)"
                    sig = parts[1] if len(parts) > 1 else "0"
                    bars = "█" * (int(sig) // 20) + "░" * (5 - int(sig) // 20)
                    lw.addItem(QListWidgetItem(f"📶  {ssid}  {bars}"))
                la.addWidget(lw)
            else:
                la.addWidget(QLabel("Nenhuma rede encontrada"))
        except:
            la.addWidget(QLabel("nmcli não disponível"))
        b = GlowButton("Fechar")
        b.clicked.connect(d.close)
        la.addWidget(b)
        d.exec_()

    def _gamepad(self):
        d, la = self._dialog("🎮  Controles", 440, 300)
        tx = QLabel(
            "Pie OS suporta qualquer controle USB ou wireless:\n\n"
            "• Xbox 360 / One / Series X|S\n"
            "• PlayStation 3 / 4 / 5\n"
            "• Nintendo Switch Pro\n"
            "• Logitech F310 / F710\n"
            "• Qualquer joystick genérico\n\n"
            "Conecte e jogue — detecção automática."
        )
        tx.setWordWrap(True)
        tx.setStyleSheet(f"color: {C['text_dim']}; font-size: 13px; padding: 8px;")
        la.addWidget(tx)
        b = GlowButton("OK")
        b.clicked.connect(d.close)
        la.addWidget(b)
        d.exec_()

    def _video(self):
        d, la = self._dialog("🖥️  Vídeo", 440, 280)
        tx = QLabel(
            "Hardware: Intel HD Graphics 3000\n\n"
            "• Modo: Tela cheia (720p)\n"
            "• VSync: Desligado\n"
            "• Aceleração: OpenGL via DRI\n"
            "• Otimizações: threaded, no-hiz\n\n"
            "Resolução atual: 1280 x 720"
        )
        tx.setStyleSheet(f"color: {C['text_dim']}; font-size: 13px; padding: 8px;")
        la.addWidget(tx)
        b = GlowButton("OK")
        b.clicked.connect(d.close)
        la.addWidget(b)
        d.exec_()

    def _audio(self):
        d, la = self._dialog("🔊  Áudio", 420, 200)
        hl = QHBoxLayout()
        vl = QLabel("Volume:")
        vl.setStyleSheet(f"color: {C['text']}; font-size: 14px;")
        hl.addWidget(vl)
        s = QSlider(Qt.Horizontal)
        s.setRange(0, 100)
        s.setValue(75)
        s.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {C["border"]}; height: 6px; border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {C["accent"]}; width: 20px; height: 20px;
                margin: -7px 0; border-radius: 10px;
            }}
            QSlider::sub-page:horizontal {{
                background: {C["accent"]}; border-radius: 3px;
            }}
        """)
        hl.addWidget(s)
        la.addLayout(hl)
        b = GlowButton("OK")
        b.clicked.connect(d.close)
        la.addWidget(b)
        d.exec_()

    def _update(self):
        d, la = self._dialog("🔄  Sistema", 420, 200)
        tx = QLabel(f"Pie OS v1.0\n\nVerificando atualizações...\n\nVocê está usando a versão mais recente.")
        tx.setStyleSheet(f"color: {C['text_dim']}; font-size: 13px; padding: 8px;")
        la.addWidget(tx)
        b = GlowButton("OK")
        b.clicked.connect(d.close)
        la.addWidget(b)
        d.exec_()

    def _about(self):
        d, la = self._dialog("ℹ️  Sobre", 460, 360)
        lo = QLabel("🍰")
        lo.setAlignment(Qt.AlignCenter)
        lo.setStyleSheet("font-size: 72px; background: transparent;")
        la.addWidget(lo)
        nm = QLabel("Pie OS")
        nm.setAlignment(Qt.AlignCenter)
        nm.setStyleSheet(f"color: {C['accent']}; font-size: 36px; font-weight: bold;")
        la.addWidget(nm)
        tx = QLabel(
            "Console System para PieBox\n"
            "Baseado em Arch Linux\n\n"
            "• Interface Xbox 360 Blades\n"
            "• Suporte: AppImage, .xex (Xenia)\n"
            "• Intel HD Graphics 3000\n"
            "• Gamepad USB/Wireless\n"
            "• WiFi • Até 300 FPS*"
        )
        tx.setAlignment(Qt.AlignCenter)
        tx.setStyleSheet(f"color: {C['text_dim']}; font-size: 13px; padding: 10px;")
        la.addWidget(tx)
        ft = QLabel("*Em jogos leves/retro. Depende do hardware.")
        ft.setAlignment(Qt.AlignCenter)
        ft.setStyleSheet(f"color: {C['text_muted']}; font-size: 10px;")
        la.addWidget(ft)
        b = GlowButton("Fechar")
        b.clicked.connect(d.close)
        la.addWidget(b)
        d.exec_()


#=============================================================================
# JANELA PRINCIPAL
#=============================================================================

class PieOSShell(QMainWindow):
    def __init__(self):
        super().__init__()
        self.blade_names = ["Início", "Jogos", "Configurações"]
        self.setup_window()
        self.setup_ui()
        self.setup_gamepad()
        self.setup_timers()
        self.apply_xbox_theme()

    def setup_window(self):
        self.setWindowTitle("Pie OS")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.showFullScreen()
        self.setCursor(Qt.BlankCursor)
        self.setStyleSheet(f"background: {C['bg']};")

    def apply_xbox_theme(self):
        self.setStyleSheet(f"""
            QMainWindow {{ background: {C["bg"]}; }}
            QWidget {{ background: transparent; }}
            QLabel {{ background: transparent; }}
        """)

    def setup_ui(self):
        mw = QWidget()
        self.setCentralWidget(mw)
        ml = QVBoxLayout(mw)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)

        self.blade_panel = BladePanel(self.blade_names)
        self.blade_panel.bladeChanged.connect(self.switch_blade)
        ml.addWidget(self.blade_panel)

        self.stack = SmoothStack()
        self.home = HomePage()
        self.games = GamesPage()
        self.settings = SettingsPage()
        self.stack.addWidget(self.home)
        self.stack.addWidget(self.games)
        self.stack.addWidget(self.settings)
        ml.addWidget(self.stack, 1)

        bar = QFrame()
        bar.setFixedHeight(44)
        bar.setStyleSheet(f"""
            QFrame {{
                background: {C["bg_blade"]};
                border-top: 1px solid {C["border"]};
            }}
        """)
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(24, 0, 24, 0)
        bl.setSpacing(20)

        hint = QLabel("🎮  Joystick: A=OK  B=Voltar  LB/RB=Guias  •  Teclado: F1-F3  F12=Desligar")
        hint.setStyleSheet(f"color: {C['text_muted']}; font-size: 11px; background: transparent;")
        bl.addWidget(hint)
        bl.addStretch()

        self.wifi_icon = QLabel("📶")
        self.wifi_icon.setStyleSheet(f"color: {C['accent']}; font-size: 14px; background: transparent;")
        bl.addWidget(self.wifi_icon)

        self.clock = QLabel("00:00")
        self.clock.setStyleSheet(f"color: {C['text']}; font-size: 14px; font-weight: bold; background: transparent;")
        bl.addWidget(self.clock)

        self.ctrl_icon = QLabel("🎮")
        self.ctrl_icon.setStyleSheet(f"color: {C['accent']}; font-size: 14px; background: transparent;")
        bl.addWidget(self.ctrl_icon)

        ml.addWidget(bar)

        self.home.launch.connect(self.launch_file)
        self.games.launch.connect(self.launch_file)

    def setup_gamepad(self):
        self.gamepad = None
        try:
            import evdev
            devs = [evdev.InputDevice(p) for p in evdev.list_devices()]
            for d in devs:
                if evdev.ecodes.EV_ABS in d.capabilities():
                    self.gamepad = d
                    self.ctrl_icon.setStyleSheet(f"color: {C['accent']}; font-size: 14px; background: transparent;")
                    print(f"Gamepad: {d.name}")
                    break
        except ImportError:
            print("evdev não disponível — use teclado")

    def setup_timers(self):
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(1000)
        self._tick()

        self.wifi_timer = QTimer(self)
        self.wifi_timer.timeout.connect(self._check_wifi)
        self.wifi_timer.start(30000)
        self._check_wifi()

    def _tick(self):
        self.clock.setText(datetime.now().strftime("%H:%M"))

    def _check_wifi(self):
        try:
            r = subprocess.run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "dev"],
                             capture_output=True, text=True, timeout=5)
            if "wifi:connected" in r.stdout.replace("\n", ":"):
                self.wifi_icon.setStyleSheet(f"color: {C['accent']}; font-size: 14px; background: transparent;")
            else:
                self.wifi_icon.setStyleSheet(f"color: {C['text_muted']}; font-size: 14px; background: transparent;")
        except:
            self.wifi_icon.setStyleSheet(f"color: {C['text_muted']}; font-size: 14px; background: transparent;")

    def switch_blade(self, idx):
        if 0 <= idx < len(self.blade_names):
            self.stack.slide_to(idx)
            self.blade_panel.set_blade(idx)

    def launch_file(self, path):
        ext = Path(path).suffix.lower()
        self.hide()
        try:
            if ext == ".appimage":
                os.chmod(path, 0o755)
                env = {**os.environ, "DISPLAY": ":0", "MESA_GL_VERSION_OVERRIDE": "3.3"}
                subprocess.run([path], env=env, timeout=600)
            elif ext == ".xex":
                subprocess.run(["/usr/bin/xenia-run", path])
            elif ext == ".sh":
                os.chmod(path, 0o755)
                subprocess.run([path], timeout=600)
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao executar:\n{e}")
        finally:
            self.showFullScreen()

    def keyPressEvent(self, e):
        k = e.key()
        m = {Qt.Key_F1: 0, Qt.Key_F2: 1, Qt.Key_F3: 2}
        if k in m:
            self.switch_blade(m[k])
        elif k == Qt.Key_Left:
            self.switch_blade(max(0, self.blade_panel.current - 1))
        elif k == Qt.Key_Right:
            self.switch_blade(min(len(self.blade_names)-1, self.blade_panel.current + 1))
        elif k == Qt.Key_Escape:
            if self.blade_panel.current != 0:
                self.switch_blade(0)
        elif k == Qt.Key_F12:
            r = QMessageBox.question(self, "Pie OS", "Desligar console?",
                                     QMessageBox.Yes | QMessageBox.No)
            if r == QMessageBox.Yes:
                subprocess.run(["poweroff"])

    def closeEvent(self, e):
        e.accept()


#=============================================================================
# MAIN
#=============================================================================

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    app.setApplicationName("Pie OS")
    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.PreferNoHinting)
    app.setFont(font)
    w = PieOSShell()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
