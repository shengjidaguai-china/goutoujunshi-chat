"""Native Jev-panel relationship trend window; all chart data stays local."""
import math

import AppKit as A
from Foundation import NSMakeRect

from overlay import ACCENT, INK, MUTED, button, color, label
from settings_ui import popup, show_window
from trend import demo_cases


def draw_text(value, x, y, size=10, tint=MUTED, bold=False):
    attrs = {A.NSFontAttributeName: (A.NSFont.boldSystemFontOfSize_ if bold else
                                    A.NSFont.systemFontOfSize_)(size),
             A.NSForegroundColorAttributeName: tint}
    A.NSString.stringWithString_(str(value)).drawAtPoint_withAttributes_((x, y), attrs)


class CandleChart(A.NSView):
    def drawRect_(self, dirty):
        bounds = self.bounds()
        color(0xFFFFFF).setFill()
        A.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(bounds, 16, 16).fill()
        trend = getattr(self, 'trend', None)
        if trend is None:
            draw_text('选择合成案例，或导入带时间戳的聊天 CSV', 34, bounds.size.height / 2, 15, MUTED)
            return
        candles = trend.candles[-45:]
        left, bottom = 62, 54
        width, height = bounds.size.width - 94, bounds.size.height - 97
        if trend.metric == 'synthetic_event_index':
            low, high = 0, 100
        else:
            low = min(0, *(c.low for c in candles))
            high = max(0, *(c.high for c in candles))
            pad = max(2, math.ceil((high - low) * .12))
            low -= pad
            high += pad
        def yy(value):
            return bottom + (value - low) * height / (high - low)
        for i in range(5):
            level = low + (high - low) * i / 4
            y = yy(level)
            color(0xE5ECE7).setStroke()
            line = A.NSBezierPath.bezierPath()
            line.moveToPoint_((left, y))
            line.lineToPoint_((left + width, y))
            line.setLineWidth_(.8)
            line.stroke()
            draw_text(f'{level:.0f}', 19, y - 6, 9)
        if low < 0 < high:
            color(0x96A89B).setStroke()
            zero = A.NSBezierPath.bezierPath()
            zero.moveToPoint_((left, yy(0)))
            zero.lineToPoint_((left + width, yy(0)))
            zero.setLineWidth_(1.1)
            zero.stroke()
        step = width / len(candles)
        body_width = min(18, max(4, step * .48))
        label_every = max(1, math.ceil(len(candles) / 8))
        for i, candle in enumerate(candles):
            x = left + step * (i + .5)
            up = candle.close >= candle.open
            tint = color(0x2D7659 if up else 0xC27A5E)
            tint.setStroke()
            wick = A.NSBezierPath.bezierPath()
            wick.moveToPoint_((x, yy(candle.low)))
            wick.lineToPoint_((x, yy(candle.high)))
            wick.setLineWidth_(2)
            wick.stroke()
            tint.setFill()
            y1, y2 = yy(candle.open), yy(candle.close)
            A.NSBezierPath.bezierPathWithRect_(NSMakeRect(
                x - body_width / 2, min(y1, y2), body_width, max(3, abs(y2-y1)))).fill()
            if i % label_every == 0 or i == len(candles)-1:
                draw_text(candle.date[5:], x-17, 22, 9)
            if candle.events:
                color(0xD8A557).setFill()
                A.NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(x-3, bottom-15, 6, 6)).fill()


class TrendWindow:
    def __init__(self, owner):
        self.owner = owner
        self.trend = None
        screen = A.NSScreen.mainScreen().visibleFrame()
        width, height = min(840, screen.size.width-50), min(650, screen.size.height-70)
        self.window = A.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, width, height), A.NSWindowStyleMaskTitled | A.NSWindowStyleMaskClosable,
            A.NSBackingStoreBuffered, False)
        self.window.setTitle_('狗头军师 · Jev 关系 K 线' + (' · 离线演示' if owner.demo else ''))
        self.window.setReleasedWhenClosed_(False)
        self.window.setLevel_(A.NSFloatingWindowLevel)
        self.window.setAppearance_(A.NSAppearance.appearanceNamed_(A.NSAppearanceNameAqua))
        view = self.window.contentView()
        view.setWantsLayer_(True)
        view.layer().setBackgroundColor_(color(0xF3F2ED).CGColor())
        label(view, '关系趋势 K 线', (26, height-53, width-52, 34), 25, True)
        self.metric_label = label(view, '请选择合成示例，或导入 CSV 查看消息净差 K 线。',
                                  (27, height-83, width-54, 24), 12, tint=MUTED)
        self.case_ids = [case_id for case_id, _ in demo_cases()]
        self.case_popup = popup(view, ['选择合成案例'] + [title for _, title in demo_cases()],
                                (26, height-131, min(270, width*.36), 31), owner, 'selectTrendCase:')
        button(view, owner, '导入聊天 CSV', 'importTrend:', (min(310, width*.39), height-131, 140, 31))
        self.summary = label(view, '仅在本机打开 CSV；不调用模型，也不保存聊天原文。',
                             (26, height-169, width-52, 26), 12, tint=INK)
        chart_height = max(225, height-298)
        self.chart = CandleChart.alloc().initWithFrame_(NSMakeRect(25, 105, width-50, chart_height))
        view.addSubview_(self.chart)
        self.events = label(view, '金色圆点标记已有事件注释；K 线只计算消息净差，需结合实际行动判断。',
                            (28, 65, width-56, 32), 11, tint=MUTED)
        label(view, '当前微信窗口 OCR 缺少完整时间线。导入 CSV 需含 timestamp,sender,message，sender 固定为 me／other。',
              (28, 20, width-56, 38), 11, tint=MUTED)
        self.window.center()
        if owner.demo:
            self.case_popup.selectItemAtIndex_(1)
            from trend import load_demo
            self.set_trend(load_demo(self.case_ids[0]))

    def set_trend(self, trend):
        self.trend = trend
        self.metric_label.setStringValue_(
            '合成事件示意指数：开高低收为手工设定，不是模型输出、爱意或关系概率。'
            if trend.metric == 'synthetic_event_index' else
            '聊天方向：对方消息 +1、我的消息 −1；不是关系评分或回复概率。')
        self.chart.trend = trend
        self.chart.setNeedsDisplay_(True)
        first, last = trend.candles[0], trend.candles[-1]
        more = ' · 图上展示最近 45 天' if len(trend.candles) > 45 else ''
        self.summary.setStringValue_(
            f'{trend.title} · {trend.messages} 条消息 / {len(trend.candles)} 个有消息的日期 · '
            f'{first.date} 至 {last.date}{more}')
        evidence = [f'{c.date[5:]} {event}' for c in trend.candles for event in c.events]
        line = '最近事件：' + '；'.join(evidence[-2:]) if evidence else '未提供事件注释；请结合邀约兑现、冲突修复和明确边界判断。'
        self.events.setStringValue_(line)
        self.events.setToolTip_(line)

    def reset(self):
        self.trend = None
        self.chart.trend = None
        self.chart.setNeedsDisplay_(True)
        self.metric_label.setStringValue_('请选择合成示例，或导入 CSV 查看消息净差 K 线。')
        self.case_popup.selectItemAtIndex_(0)
        self.summary.setStringValue_('仅在本机打开 CSV；不调用模型，也不保存聊天原文。')
        self.events.setStringValue_('金色圆点标记已有事件注释；K 线只计算消息净差，需结合实际行动判断。')

    def show(self):
        show_window(self.window)
