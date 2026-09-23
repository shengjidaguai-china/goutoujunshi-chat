# -*- coding: utf-8 -*-
"""识别调试窗：把子进程送来的帧和每个 OCR 框按分类画出来，看识别到底哪儿错了。
帧只在内存里画（QImage 拿 bytes 建），不存图、不进日志。"""
from datetime import datetime

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QImage, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import PlainTextEdit

# (kind, 画框的色, 色的中文, 这类是什么)：跟设置页那条提示一个口径
_KINDS = (("me", "#18794e", "绿", "我"), ("her", "#1f6fd0", "蓝", "对方"),
          ("gray", "#8a8a8a", "灰", "过滤掉的灰字"), ("name", "#e08b18", "橙", "当成发言人名"),
          ("image", "#d0342c", "红", "当成图片丢掉"), ("tiny", "#d4b106", "黄", "小字丢掉"))
_COLOR = {k: c for k, c, _, _ in _KINDS}
_NAME = {k: n for k, _, _, n in _KINDS}
_AREA = "#1f6fd0"  # 消息区
_HEAD = "#8b5cf6"  # 头部（会话名那条）


class _Canvas(QWidget):
    """左边那块画布：整帧等比缩放铺满，再按同一个倍率把各种框套上去。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.img = None
        self.pkt = None
        self.setMinimumSize(320, 240)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#1b1f1d"))
        if self.img is None:
            p.setPen(QColor("#9aa6a0"))
            p.drawText(self.rect(), Qt.AlignCenter, "等待画面…\n开着采集，微信有动静就会有帧")
            return
        # 等比铺满 + 居中；s 是「缩小后的帧 → 控件」的倍率，k 是子进程缩了多少
        s = min(self.width() / self.img.width(), self.height() / self.img.height())
        w, h = self.img.width() * s, self.img.height() * s
        ox, oy = (self.width() - w) / 2, (self.height() - h) / 2
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.drawImage(QRectF(ox, oy, w, h), self.img)
        k = self.pkt.get("scale", 1) or 1
        f = lambda x, y: (ox + x * s / k, oy + y * s / k)  # 原帧坐标 → 控件坐标
        area = self.pkt.get("area")
        if not area:
            p.setPen(QColor("#d0342c"))
            p.drawText(QRectF(ox, oy, w, 30), Qt.AlignCenter, "认不出消息区")
            return
        x0, y0, x1, y1 = area
        p.setPen(QPen(QColor(_HEAD), 1))
        p.drawRect(QRectF(*f(x0, self.pkt.get("pane_top", 0)),
                          (x1 - x0) * s / k, (y0 - self.pkt.get("pane_top", 0)) * s / k))
        p.setPen(QPen(QColor(_AREA), 2))
        p.drawRect(QRectF(*f(x0, y0), (x1 - x0) * s / k, (y1 - y0) * s / k))
        tag = QFont(self.font())
        tag.setPointSizeF(7.5)
        p.setFont(tag)
        fm = QFontMetricsF(tag)
        for bx0, by0, bx1, by1, kind, _text in self.pkt.get("boxes", ()):
            color = QColor(_COLOR.get(kind, "#ffffff"))
            p.setPen(QPen(color, 2))
            left, top = f(x0 + bx0, y0 + by0)
            p.drawRect(QRectF(left, top, (bx1 - bx0) * s / k, (by1 - by0) * s / k))
            # 小标签贴在框左上角外侧；宽度按文字实际宽度来，别糊住旁边的框
            label = QRectF(left, top - 12, fm.horizontalAdvance(kind) + 6, 12)
            p.fillRect(label, color)
            p.setPen(QColor("#ffffff"))
            p.drawText(label, Qt.AlignCenter, kind)


class DebugWindow(QWidget):
    """独立小窗，Qt.Tool 不占任务栏。show_packet() 喂一帧就重画一次；关窗回调把设置里的开关拨回去。"""

    def __init__(self, on_close=None):
        super().__init__()
        self.on_close = on_close
        self.setWindowTitle("识别调试")
        self.setWindowFlags(Qt.Tool)
        self.resize(900, 650)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 8)
        outer.setSpacing(8)
        row = QHBoxLayout()
        row.setSpacing(8)
        self.canvas = _Canvas(self)
        row.addWidget(self.canvas, 1)
        self.info = PlainTextEdit(self)
        self.info.setReadOnly(True)
        self.info.setFixedWidth(300)
        self.info.setPlainText(_legend())
        row.addWidget(self.info)
        outer.addLayout(row)
        self.status = QLabel("最近一帧 —— · 等待中…", self)
        self.status.setStyleSheet("color: #68776f;")
        outer.addWidget(self.status)

    def show_packet(self, pkt):
        """子进程送来的一帧：RGB 裸字节 → QImage（copy 一份，原 bytes 之后就回收了）。"""
        self.canvas.img = QImage(pkt["rgb"], pkt["w"], pkt["h"], pkt["w"] * 3,
                                 QImage.Format_RGB888).copy()
        self.canvas.pkt = pkt
        self.canvas.update()
        area = pkt.get("area")
        counts = {}
        for b in pkt.get("boxes", ()):
            counts[b[4]] = counts.get(b[4], 0) + 1
        text = [
            f"会话：{pkt.get('title') or '（未识别）'}",
            "消息区：" + (f"x {area[0]}–{area[2]} · y {area[1]}–{area[3]}" if area else "认不出消息区"),
            f"头部顶：y {pkt.get('pane_top', 0)}",
            f"OCR 耗时：{pkt.get('ocr_ms', 0)} ms",
            f"帧：{pkt['w']}×{pkt['h']}（原帧缩了 1/{pkt.get('scale', 1)} 再过队列）",
            "框：" + ("、".join(f"{_NAME.get(k, k)} {v}" for k, v in counts.items()) or "无"),
            "",
            f"本帧 {len(pkt.get('lines', ()))} 行",
        ]
        for who, name, line in pkt.get("lines", ()):
            text.append(f"{who}({name})：{line}" if name else f"{who}：{line}")
        text += ["", _legend()]
        self.info.setPlainText("\n".join(text))
        stamp = datetime.fromtimestamp(pkt.get("ts") or 0).strftime("%H:%M:%S")
        self.status.setText(f"最近一帧 {stamp} · 共 {len(pkt.get('boxes', ()))} 个框")

    def closeEvent(self, event):
        if self.on_close:
            self.on_close()
        super().closeEvent(event)


def _legend():
    return ("图例（蓝粗框 = 消息区，紫细框 = 头部会话名）\n"
            + "\n".join(f"  {word} = {what}（{k}）" for k, _, word, what in _KINDS))
