"""Readable native analysis cards and a separate transcript-review tab."""
import math
import AppKit as A
from Foundation import NSMakeRect
from overlay import ACCENT, INK, MUTED, button, color, label
from settings_ui import field, popup, show_window
from ranking import EXPLANATION
from core import intent_confidence_label, INTENT_CONFIDENCE_NOTE


def surface(parent, frame, tint=0xFFFFFF):
    view = A.NSView.alloc().initWithFrame_(NSMakeRect(*frame))
    view.setWantsLayer_(True)
    view.layer().setCornerRadius_(16)
    view.layer().setBackgroundColor_(color(tint).CGColor())
    parent.addSubview_(view)
    return view


def text_height(text, width, size=14, bold=False):
    font = (A.NSFont.boldSystemFontOfSize_ if bold else A.NSFont.systemFontOfSize_)(size)
    rect = A.NSString.stringWithString_(text).boundingRectWithSize_options_attributes_(
        (width, 100000), A.NSStringDrawingUsesLineFragmentOrigin, {A.NSFontAttributeName: font})
    return max(22, math.ceil(rect.size.height)+8)


class AnalysisScreen:
    def __init__(self, owner):
        self.owner = owner
        self.last_key = None
        frame = A.NSScreen.mainScreen().visibleFrame()
        self.width = min(760, frame.size.width-50)
        self.height = min(710, frame.size.height-70)
        w, h = self.width, self.height
        self.window = A.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, w, h), A.NSWindowStyleMaskTitled | A.NSWindowStyleMaskClosable |
            A.NSWindowStyleMaskMiniaturizable, A.NSBackingStoreBuffered, False)
        self.window.setTitle_('狗头军师 · 详细分析' + (' · 离线演示' if owner.demo else ''))
        self.window.setReleasedWhenClosed_(False)
        self.window.setLevel_(A.NSFloatingWindowLevel)
        self.window.setAppearance_(A.NSAppearance.appearanceNamed_(A.NSAppearanceNameAqua))
        view = self.window.contentView()
        view.setWantsLayer_(True)
        view.layer().setBackgroundColor_(color(0xF3F2ED).CGColor())
        label(view, '狗头军师', (26, h-52, w-170, 32), 25, True)
        self.subtitle = label(view, '看清局面，再决定下一句', (27, h-79, w-80, 23), 12, tint=MUTED)
        button(view, owner, '设置', 'settings:', (w-100, h-53, 74, 31))
        self.tabs = A.NSSegmentedControl.alloc().initWithFrame_(NSMakeRect(24, h-125, w-48, 32))
        self.tabs.setSegmentCount_(2)
        for i, title in enumerate(('分析详情', '核对原文')):
            self.tabs.setLabel_forSegment_(title, i)
            self.tabs.setWidth_forSegment_((w-50)/2, i)
        self.tabs.setSelectedSegment_(0)
        self.tabs.setTarget_(owner)
        self.tabs.setAction_('detailTab:')
        view.addSubview_(self.tabs)
        self.viewport = h-198
        self.scroll = A.NSScrollView.alloc().initWithFrame_(NSMakeRect(24, 63, w-48, self.viewport))
        self.scroll.setDrawsBackground_(False)
        self.scroll.setHasVerticalScroller_(True)
        self.scroll.setAutohidesScrollers_(True)
        self.scroll.setBorderType_(A.NSNoBorder)
        view.addSubview_(self.scroll)
        self.review = surface(view, (24, 63, w-48, self.viewport))
        rw, rh = w-48, self.viewport
        label(self.review, '核对后再分析', (20, rh-40, rw-40, 25), 17, True)
        label(self.review, '可直接粘贴对话，也可以读取当前聊天窗口。', (20, rh-65, rw-40, 22), 12, tint=MUTED)
        owner.title_field = field(self.review, '', (20, rh-109, (rw-52)*.56, 30))
        owner.title_field.setPlaceholderString_('会话标题或对象称呼')
        owner.scene = popup(self.review, ['日常回复', '邀约推进', '冲突修复', '投入与退出'],
                            (rw*.59, rh-109, rw*.41-20, 30))
        editor = A.NSScrollView.alloc().initWithFrame_(NSMakeRect(20, 188, rw-40, max(60, rh-313)))
        editor.setHasVerticalScroller_(True)
        editor.setWantsLayer_(True)
        editor.layer().setCornerRadius_(10)
        owner.transcript = A.NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, rw-58, max(60, rh-313)))
        owner.transcript.setFont_(A.NSFont.systemFontOfSize_(14))
        owner.transcript.setTextColor_(INK)
        owner.transcript.setBackgroundColor_(color(0xF5F4EF))
        owner.transcript.setTextContainerInset_((12, 12))
        owner.transcript.setRichText_(False)
        owner.transcript.setVerticallyResizable_(True)
        owner.transcript.setHorizontallyResizable_(False)
        owner.transcript.setAutoresizingMask_(A.NSViewWidthSizable)
        owner.transcript.textContainer().setWidthTracksTextView_(True)
        editor.setDocumentView_(owner.transcript)
        self.review.addSubview_(editor)
        label(self.review, '请检查“我／对方”归属、错字和遗漏。', (20, 164, rw-40, 22), 11, tint=MUTED)
        owner.background = field(self.review, '', (20, 127, rw-40, 30))
        owner.background.setPlaceholderString_('补充背景或本轮目标（可选）')
        owner.confirm = A.NSButton.alloc().initWithFrame_(NSMakeRect(20, 91, rw-40, 27))
        owner.confirm.setButtonType_(A.NSSwitchButton)
        owner.confirm.setTitle_('已核对原文，同意交给配置的策略与回复服务分析')
        owner.confirm.setFont_(A.NSFont.systemFontOfSize_(12))
        self.review.addSubview_(owner.confirm)
        owner.route = label(self.review, '', (21, 57, rw-42, 32), 10, tint=MUTED)
        self.read_button = button(self.review, owner, '读取当前聊天', 'capture:', (20, 16, 130, 33))
        self.clear_button = button(self.review, owner, '清空本轮', 'clear:', (158, 16, 110, 33))
        owner.auto_read = A.NSButton.alloc().initWithFrame_(NSMakeRect(rw-176, 19, 156, 28))
        owner.auto_read.setButtonType_(A.NSSwitchButton)
        owner.auto_read.setTitle_('自动读取对话')
        owner.auto_read.setFont_(A.NSFont.systemFontOfSize_(12))
        owner.auto_read.setTarget_(owner)
        owner.auto_read.setAction_('autoRead:')
        owner.auto_read.setEnabled_(not owner.demo)
        self.review.addSubview_(owner.auto_read)
        self.primary = button(view, owner, '重新分析', 'detailAnalyze:', (24, 15, 120, 34), True)
        self.rewrite = button(view, owner, '更像我一点', 'rewriteReplies:', (153, 15, 125, 34))
        self.rewrite.setToolTip_('参考当前对话中你的可靠原话，只改写回复并重新排序；不训练模型。')
        owner.status = label(view, '先读取或粘贴对话', (295, 15, w-320, 36), 11, tint=MUTED)
        self.window.center()
        self.select_tab(0)

    def select_tab(self, index):
        self.tabs.setSelectedSegment_(index)
        self.review.setHidden_(index != 1)
        self.scroll.setHidden_(index == 1)
        self.primary.setTitle_('确认并分析' if index == 1 else '重新分析')

    def show(self, tab=0):
        self.select_tab(tab)
        self.sync()
        show_window(self.window)

    def sync(self):
        owner = self.owner
        self.primary.setEnabled_(not owner.busy)
        self.read_button.setEnabled_(not owner.busy)
        self.clear_button.setEnabled_(not owner.busy)
        self.rewrite.setEnabled_(not owner.busy and bool(owner.session.advice and owner.session.advice['candidates']))
        owner.status.setToolTip_(owner.status.stringValue())
        profile = owner.conversations.current
        name = profile['label'] if profile['label'] != '当前会话' else owner.title_field.stringValue() or '当前对象'
        self.subtitle.setStringValue_(f"{name} · {profile['stage']} · {profile['goal']}" + (' · 离线示例' if owner.demo else ''))
        advice = owner.session.advice
        key = repr((advice, owner.busy, bool(owner.result_capture), owner.demo))
        if key == self.last_key:
            return
        same_advice = repr(advice) == getattr(self, 'advice_key', None)
        self.advice_key = repr(advice)
        self.last_key = key
        old_offset = self.scroll.contentView().bounds().origin.y
        old_height = getattr(self, 'document_height', self.viewport)
        width = self.width-64
        blocks = []
        def block(title, body, tint=0xFFFFFF, size=14):
            blocks.append(('text', title, body, tint, size, 56+text_height(body, width-40, size)))
        if not advice:
            block('还没有本轮分析', '先到“核对原文”读取或粘贴对话，确认后即可查看判断依据、下一步与回复建议。', 0xE7EFE9, 16)
        else:
            intent = advice.get('intent') or '；'.join(advice['hypotheses']) or '证据不足，暂无法判断。'
            block('对方可能的意图', intent + '\n' + intent_confidence_label(advice), 0xE7EFE9, 18)
            block('军师建议 · ' + advice['strategy'], advice['recommendation'], 0xFFFFFF, 16)
            if advice['support']:
                block('先照顾好自己的感受', advice['support'])
            for title, key_name, fallback in (
                ('已知事实', 'facts', '暂无足够的可见证据'),
                ('合理推测', 'hypotheses', '暂不推断'),
                ('还需要确认', 'unknowns', '本轮没有额外的关键未知')):
                block(title, '\n'.join('• ' + x for x in advice[key_name]) or fallback)
            block('下一步', advice['next_step'])
            block('什么时候停下来', advice['stop_condition'], 0xFFF6E9)
            if advice['question']:
                block('军师想确认', advice['question'])
            block('候选回复排序', '排序暂不可用，以下保留生成顺序。' if advice.get('ranking_status') == 'unavailable' else
                  (EXPLANATION + (' 当前权重为离线演示数字。' if owner.demo else '')), size=12)
            for i, row in enumerate(advice['candidates']):
                body = row['text']
                detail = '理由：' + row['reason'] + '\n代价：' + row['tradeoff']
                title = f"#{i+1}" + (f" · {row['weight']}%" if 'weight' in row else ' · 待排序')
                height = 110+text_height(body, width-40, 18)+text_height(detail, width-40, 12)
                blocks.append(('reply', title, body, 0xE7EFE9 if i == 0 else 0xFFFFFF, 18, height, detail, i))
            if not advice['candidates']:
                block('本轮不提供候选', '按上方军师建议行动，无需为了延续话题勉强回复。')
            decision = advice.get('jev_decision')
            block('如何理解意图把握', INTENT_CONFIDENCE_NOTE, size=12)
            if decision:
                block('策略判断依据', f"Jev 选择「{decision['strategy']}」，策略置信度 {decision['confidence']:.0%}。\n这反映模型对策略选择的判断，不是回复成功率，也不是候选推荐权重。", size=12)
        height = max(self.viewport, sum(b[5]+12 for b in blocks))
        doc = A.NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))
        y = height
        for b in blocks:
            kind, title, body, tint, size, bh = b[:6]
            y -= bh
            card = surface(doc, (0, y, width, bh), tint)
            label(card, title, (20, bh-38, width-40, 25), 14, True, ACCENT if tint == 0xE7EFE9 else INK)
            th = text_height(body, width-40, size)
            label(card, body, (20, bh-44-th, width-40, th), size)
            if kind == 'reply':
                detail, index = b[6:]
                dh = text_height(detail, width-40, 12)
                label(card, detail, (20, 53, width-40, dh), 12, tint=MUTED)
                for title, action, x, filled in [('复制', 'copyCandidate:', 20, False), ('填入', 'fillCandidate:', 112, True)]:
                    control = button(card, owner, title, action, (x, 12, 82, 31), filled)
                    control.setTag_(index)
                    control.setEnabled_(not owner.busy and (not filled or (not owner.demo and owner.result_capture is not None)))
            y -= 12
        self.scroll.setDocumentView_(doc)
        self.document_height = height
        offset = max(0, min(height-self.viewport, old_offset+height-old_height)) if same_advice else max(0, height-self.viewport)
        self.scroll.contentView().scrollToPoint_((0, offset))
        self.scroll.reflectScrolledClipView_(self.scroll.contentView())
