"""Native borderless bubble and reply panel; no screen capture or network here."""
import math

import AppKit as A
import Quartz  # Registers CGColor bridge metadata used by CALayer.
import objc
from Foundation import NSMakeRect
from ranking import EXPLANATION
from core import intent_confidence_label, INTENT_CONFIDENCE_NOTE


def color(hex_value, alpha=1):
    return A.NSColor.colorWithSRGBRed_green_blue_alpha_(
        ((hex_value >> 16) & 255) / 255, ((hex_value >> 8) & 255) / 255,
        (hex_value & 255) / 255, alpha)


ACCENT = color(0x30584A)
INK = color(0x26352F)
MUTED = color(0x68736C)


class OverlayPanel(A.NSPanel):
    def canBecomeKeyWindow(self):
        return True

    def canBecomeMainWindow(self):
        return False


class RoundedSurface(A.NSView):
    def drawRect_(self, dirty):
        color(0xFCFAF6, getattr(self, "opacity", .92)).setFill()
        shape = A.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            A.NSInsetRect(self.bounds(), 1, 1), 24, 24)
        shape.fill()
        color(0xD7DDD6, .8).setStroke()
        shape.setLineWidth_(1)
        shape.stroke()

    def mouseDown_(self, event):
        self.window().performWindowDragWithEvent_(event)


class BubbleView(A.NSView):
    def drawRect_(self, dirty):
        ACCENT.setFill()
        A.NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(3, 3, 60, 60)).fill()
        attrs = {A.NSFontAttributeName: A.NSFont.boldSystemFontOfSize_(17),
                 A.NSForegroundColorAttributeName: A.NSColor.whiteColor()}
        A.NSString.stringWithString_("军师").drawInRect_withAttributes_(NSMakeRect(15, 22, 43, 23), attrs)
        A.NSColor.whiteColor().setFill()
        A.NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(48, 48, 17, 17)).fill()
        color(0xEAA345 if self.owner.busy else 0x28AA68).setFill()
        A.NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(51, 51, 11, 11)).fill()

    def accessibilityPerformPress(self):
        self.owner.toggleOverlay_(None)
        return True

    def mouseDown_(self, event):
        self.start_mouse = A.NSEvent.mouseLocation()
        self.start_origin = self.window().frame().origin
        self.dragged = False

    def mouseDragged_(self, event):
        point = A.NSEvent.mouseLocation()
        dx, dy = point.x - self.start_mouse.x, point.y - self.start_mouse.y
        if abs(dx) + abs(dy) < 4 and not self.dragged:
            return
        self.dragged = True
        screen = (self.window().screen() or A.NSScreen.mainScreen()).visibleFrame()
        x = max(screen.origin.x, min(self.start_origin.x + dx, A.NSMaxX(screen) - 68))
        y = max(screen.origin.y, min(self.start_origin.y + dy, A.NSMaxY(screen) - 68))
        self.window().setFrameOrigin_((x, y))
        self.owner.overlay.position_panel()

    def mouseUp_(self, event):
        if not self.dragged:
            self.owner.toggleOverlay_(None)

    def rightMouseDown_(self, event):
        menu = A.NSMenu.alloc().initWithTitle_("狗头军师")
        for title, action in (("设置", "settings:"), ("详细分析", "details:"),
                              ("关系 K 线", "trend:"), ("退出狗头军师", "quit:")):
            item = menu.addItemWithTitle_action_keyEquivalent_(title, action, "")
            item.setTarget_(self.owner)
        A.NSMenu.popUpContextMenu_withEvent_forView_(menu, event, self)


def window(width, height):
    panel = OverlayPanel.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(0, 0, width, height),
        A.NSWindowStyleMaskBorderless | A.NSWindowStyleMaskNonactivatingPanel,
        A.NSBackingStoreBuffered, False)
    panel.setOpaque_(False)
    panel.setBackgroundColor_(A.NSColor.clearColor())
    panel.setHasShadow_(True)
    panel.setLevel_(A.NSFloatingWindowLevel)
    panel.setHidesOnDeactivate_(False)
    panel.setReleasedWhenClosed_(False)
    panel.setCollectionBehavior_(A.NSWindowCollectionBehaviorCanJoinAllSpaces |
                                 A.NSWindowCollectionBehaviorFullScreenAuxiliary)
    panel.setAppearance_(A.NSAppearance.appearanceNamed_(A.NSAppearanceNameAqua))
    return panel


def label(parent, text, frame, size=15, bold=False, tint=INK):
    field = A.NSTextField.wrappingLabelWithString_(text)
    field.setFrame_(NSMakeRect(*frame))
    field.setFont_((A.NSFont.boldSystemFontOfSize_ if bold else A.NSFont.systemFontOfSize_)(size))
    field.setTextColor_(tint)
    parent.addSubview_(field)
    return field


def button(parent, owner, title, action, frame, filled=False, symbol=None):
    control = A.NSButton.alloc().initWithFrame_(NSMakeRect(*frame))
    control.setTitle_(title)
    control.setBordered_(False)
    control.setTarget_(owner)
    control.setAction_(action)
    control.setFont_(A.NSFont.boldSystemFontOfSize_(15))
    control.setContentTintColor_(A.NSColor.whiteColor() if filled else ACCENT)
    if symbol:
        control.setImage_(A.NSImage.imageWithSystemSymbolName_accessibilityDescription_(symbol, title))
        control.setImagePosition_(A.NSImageOnly)
        control.setContentTintColor_(MUTED)
        control.setToolTip_(title)
        control.setAccessibilityLabel_(title)
    else:
        control.setWantsLayer_(True)
        control.layer().setCornerRadius_(frame[3] / 2)
        control.layer().setBackgroundColor_((ACCENT if filled else A.NSColor.whiteColor()).CGColor())
        if not filled:
            control.layer().setBorderWidth_(1)
            control.layer().setBorderColor_(color(0xD7DDD6).CGColor())
    parent.addSubview_(control)
    return control


class ReplyOverlay:
    def __init__(self, owner):
        self.owner = owner
        self.last_content = None
        self.expanded = set()
        self.panel = window(420, 640)
        self.panel.setTitle_("狗头军师 · 回复悬浮窗")
        surface = RoundedSurface.alloc().initWithFrame_(NSMakeRect(0, 0, 420, 640))
        self.panel.setContentView_(surface)
        label(surface, "狗头军师", (22, 582, 275, 30), 21, True)
        self.surface = surface
        button(surface, owner, "K线", "trend:", (277, 585, 45, 28))
        button(surface, owner, "设置", "settings:", (329, 585, 28, 28), symbol="gearshape")
        button(surface, owner, "收起悬浮窗", "collapseOverlay:", (374, 585, 25, 28), symbol="xmark")
        self.subtitle = label(surface, "先读取对话，再让军师帮你想下一句", (23, 551, 338, 24), 11, tint=MUTED)
        button(surface, owner, "切换对象或目标", "settings:", (365, 551, 26, 23), symbol="person.crop.circle")
        self.scroll = A.NSScrollView.alloc().initWithFrame_(NSMakeRect(18, 80, 384, 465))
        self.scroll.setDrawsBackground_(False)
        self.scroll.setHasVerticalScroller_(True)
        self.scroll.setAutohidesScrollers_(True)
        self.scroll.setBorderType_(A.NSNoBorder)
        surface.addSubview_(self.scroll)
        self.refresh = button(surface, owner, "读取对话", "refreshOverlay:", (22, 37, 116, 34))
        self.rewrite = button(surface, owner, "更像我一点", "rewriteReplies:", (145, 37, 126, 34))
        self.rewrite.setToolTip_("参考本轮对话中你的用词和句长，只改写回复并重新评分；不跨会话训练模型。")
        button(surface, owner, "详细分析", "details:", (278, 37, 120, 34))
        self.status = label(surface, "", (24, 9, 372, 23), 10, tint=MUTED)
        self.bubble = window(68, 68)
        self.bubble.setTitle_("狗头军师悬浮球")
        self.bubble_view = BubbleView.alloc().initWithFrame_(NSMakeRect(0, 0, 68, 68))
        self.bubble_view.owner = owner
        self.bubble_view.setAccessibilityElement_(True)
        self.bubble_view.setAccessibilityRole_(A.NSAccessibilityButtonRole)
        self.bubble_view.setAccessibilityLabel_("狗头军师，点击展开，拖动移动，右键设置或退出")
        self.bubble.setContentView_(self.bubble_view)
        frame = A.NSScreen.mainScreen().visibleFrame()
        self.bubble.setFrameOrigin_((A.NSMaxX(frame) - 500, A.NSMaxY(frame) - 160))
        self.position_panel()
        self.bubble.orderFrontRegardless()
        self.panel.orderFrontRegardless()

    def show_review(self, transcript):
        self.reviewing = True
        doc = A.NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 372, 399))
        label(doc, "核对本轮对话", (12, 360, 348, 28), 18, True)
        label(doc, "确认后将文字交给 Jev 和回复模型分析", (12, 332, 348, 23), 12, tint=MUTED)
        scroll = A.NSScrollView.alloc().initWithFrame_(NSMakeRect(12, 73, 348, 251))
        scroll.setHasVerticalScroller_(True)
        self.review_text = A.NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 328, 251))
        self.review_text.setFont_(A.NSFont.systemFontOfSize_(14))
        self.review_text.setRichText_(False)
        self.review_text.setTextContainerInset_((8, 8))
        self.review_text.setAutoresizingMask_(A.NSViewWidthSizable)
        self.review_text.textContainer().setWidthTracksTextView_(True)
        self.review_text.setString_(transcript)
        scroll.setDocumentView_(self.review_text)
        doc.addSubview_(scroll)
        button(doc, self.owner, "确认并分析", "confirmOverlay:", (85, 17, 202, 40), True)
        self.scroll.setDocumentView_(doc)
        self.scroll.contentView().scrollToPoint_((0, 0))
        self.panel.makeKeyAndOrderFront_(None)

    def position_panel(self):
        frame = self.bubble.frame()
        screen = (self.bubble.screen() or A.NSScreen.mainScreen()).visibleFrame()
        x = max(screen.origin.x + 8, min(frame.origin.x, A.NSMaxX(screen) - 428))
        y = max(screen.origin.y + 8, min(frame.origin.y - 648, A.NSMaxY(screen) - 648))
        self.panel.setFrameOrigin_((x, y))

    def toggle_reason(self, index):
        if index in self.expanded:
            self.expanded.remove(index)
        else:
            self.expanded.add(index)
        self.sync(self.owner.session.advice, str(self.owner.status.stringValue()), self.owner.busy)

    def sync(self, advice, status, busy):
        self.status.setStringValue_(status)
        self.status.setToolTip_(status)
        self.bubble_view.setNeedsDisplay_(True)
        self.refresh.setEnabled_(not busy)
        self.rewrite.setEnabled_(not busy and bool(advice and advice['candidates']))
        self.refresh.setTitle_("处理中…" if busy else ("重新分析" if advice else "读取对话"))
        profile = self.owner.conversations.current
        name = profile['label'] if profile['label'] != '当前会话' else str(self.owner.title_field.stringValue()) or '当前对象'
        subtitle = f"{name} · {profile['stage']} · {profile['goal']}"
        if self.owner.demo:
            subtitle = '演示对象 A · 了解中 · 自然接话（离线示例）'
        self.subtitle.setStringValue_(subtitle)
        self.subtitle.setToolTip_(subtitle)
        # Disable old actions while a request is in progress even without a redraw.
        for i, control in enumerate(self.owner.candidate_buttons):
            available = bool(advice and control.tag() < len(advice['candidates'])) and not busy
            if i % 2:
                captured = self.owner.result_capture
                available = available and not self.owner.demo and captured is not None and bool(captured.title)
            control.setEnabled_(available)
        if getattr(self, 'reviewing', False):
            return
        advice_key = repr(advice)
        if advice_key != getattr(self, 'advice_key', None):
            self.expanded.clear()
            self.advice_key = advice_key
        content = repr((advice, sorted(self.expanded)))
        if content == self.last_content:
            return
        previous_scroll = self.scroll.contentView().bounds().origin.y
        same_advice = getattr(self, 'rendered_advice', None) == advice_key
        self.last_content = content
        self.rendered_advice = advice_key
        self.owner.candidate_buttons = []
        candidates = advice['candidates'] if advice else []

        def text_height(text, size, width=342, bold=False):
            font = (A.NSFont.boldSystemFontOfSize_ if bold else A.NSFont.systemFontOfSize_)(size)
            bounds = A.NSString.stringWithString_(text).boundingRectWithSize_options_attributes_(
                (width, 10000), A.NSStringDrawingUsesLineFragmentOrigin, {A.NSFontAttributeName: font})
            return max(22, math.ceil(bounds.size.height) + 6)

        summary = []
        if advice:
            intent = advice.get('intent') or (advice['hypotheses'][0] if advice['hypotheses'] else '证据不足，暂无法判断')
            basis = '依据：' + (advice['facts'][0] if advice['facts'] else '目前没有足够的可见证据')
            summary = [('对方可能的意图', 16, True, INK), (intent, 16, True, INK),
                       (intent_confidence_label(advice), 12, False, MUTED),
                       (basis, 12, False, MUTED), ('军师建议 · ' + advice['strategy'], 15, True, color(0x30584A)),
                       (advice['recommendation'], 14, False, INK)]
        summary_height = sum(text_height(t, z, bold=b) + 7 for t, z, b, _ in summary) + (39 if advice else 0)
        rows = candidates or [{'text': advice['recommendation'] if advice else
                               '打开聊天，点击“读取对话”。核对文字后，军师会分析意图并给出回复建议。'}]
        heights = []
        for i, row in enumerate(rows):
            h = 122 + text_height(row['text'], 18) if candidates else 65 + text_height(row['text'], 17)
            if candidates and i in self.expanded:
                h += text_height('理由：' + row['reason'], 12) + text_height('代价：' + row['tradeoff'], 12) + 14
            heights.append(h)
        height = max(465, summary_height + sum(heights) + 12 * len(rows))
        doc = A.NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 372, height))
        self.scroll.setDocumentView_(doc)
        y = height
        for text, size, bold, tint in summary:
            h = text_height(text, size, bold=bold)
            y -= h
            field = label(doc, text, (12, y, 348, h), size, bold, tint)
            if text.startswith('判断把握'):
                field.setToolTip_(INTENT_CONFIDENCE_NOTE)
            y -= 7
        if advice:
            y -= 30
            label(doc, '候选回复排序', (12, y, 200, 24), 13, tint=MUTED)
            button(doc, self.owner, '推荐权重说明', 'rankingInfo:', (326, y, 25, 24), symbol='info.circle')
            if advice.get('ranking_status') == 'unavailable':
                label(doc, '排序暂不可用', (175, y, 150, 24), 11, tint=MUTED)
            y -= 9
        for i, (row, h) in enumerate(zip(rows, heights)):
            y -= h
            card = A.NSView.alloc().initWithFrame_(NSMakeRect(0, y, 372, h))
            card.setWantsLayer_(True)
            card.layer().setCornerRadius_(18)
            card.layer().setBackgroundColor_(color(0xE7EFE9 if i == 0 else 0xF2F1EC).CGColor())
            doc.addSubview_(card)
            weight = f"{row['weight']}%" if 'weight' in row else '待排序'
            title = f"#{i+1} · {weight}" if candidates else ('本轮建议 · 无候选' if advice else '等待分析')
            heading = label(card, title, (15, h-32, 342, 23), 14, True, ACCENT)
            heading.setToolTip_(EXPLANATION if candidates else title)
            th = text_height(row['text'], 18 if candidates else 17)
            text_y = h - 39 - th
            label(card, row['text'], (15, text_y, 342, th), 18 if candidates else 17)
            if candidates:
                cy = text_y - 38
                copy = button(card, self.owner, '复制', 'copyCandidate:', (15, cy, 82, 32))
                copy.setTag_(i)
                copy.setEnabled_(not busy)
                fill = button(card, self.owner, '填入', 'fillCandidate:', (108, cy, 82, 32), True)
                fill.setTag_(i)
                fill.setEnabled_(not busy and not self.owner.demo and self.owner.result_capture is not None)
                self.owner.candidate_buttons += [copy, fill]
                toggle = button(card, self.owner, '收起理由' if i in self.expanded else '为什么这样回',
                                'toggleReason:', (15, cy-29, 135, 24))
                toggle.setBordered_(False)
                toggle.setTag_(i)
                toggle.setFont_(A.NSFont.systemFontOfSize_(11))
                if i in self.expanded:
                    dy = cy-37
                    for text in ('理由：' + row['reason'], '代价：' + row['tradeoff']):
                        dh = text_height(text, 12)
                        dy -= dh
                        label(card, text, (15, dy, 342, dh), 12, tint=MUTED)
                        dy -= 7
            y -= 12
        # Keep the visible top while a disclosure changes document height.
        old_height = getattr(self, 'document_height', height)
        self.document_height = height
        target = max(0, min(height-465, previous_scroll + height-old_height)) if same_advice else max(0, height-465)
        self.scroll.contentView().scrollToPoint_((0, target))
        self.scroll.reflectScrolledClipView_(self.scroll.contentView())
