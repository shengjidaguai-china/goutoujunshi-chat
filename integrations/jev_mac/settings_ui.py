"""Native settings matching the approved two-column design."""
import os
import AppKit as A
from Foundation import NSMakeRect
from overlay import ACCENT, INK, MUTED, button, color, label
from experience import STAGES, GOALS, TONES, LENGTHS
from client import read_deepseek_keychain
from jev import read_keychain as read_jev_keychain


def card(parent, x, y, width, height, title):
    view = A.NSView.alloc().initWithFrame_(NSMakeRect(x, y, width, height))
    view.setWantsLayer_(True)
    view.layer().setCornerRadius_(18)
    view.layer().setBackgroundColor_(A.NSColor.whiteColor().CGColor())
    parent.addSubview_(view)
    label(view, title, (20, height-44, width-40, 28), 19, True)
    return view


def field(parent, text, frame):
    control = A.NSTextField.alloc().initWithFrame_(NSMakeRect(*frame))
    control.setStringValue_(text)
    control.setFont_(A.NSFont.systemFontOfSize_(14))
    control.setTextColor_(INK)
    control.setBezeled_(False)
    control.setDrawsBackground_(True)
    control.setBackgroundColor_(color(0xF2F1EC))
    parent.addSubview_(control)
    return control


def secure_field(parent, frame):
    control = A.NSSecureTextField.alloc().initWithFrame_(NSMakeRect(*frame))
    control.setFont_(A.NSFont.systemFontOfSize_(14))
    control.setPlaceholderString_('输入新 Key；留空不会改动已保存的 Key')
    parent.addSubview_(control)
    return control


def popup(parent, items, frame, owner=None, action=None):
    control = A.NSPopUpButton.alloc().initWithFrame_pullsDown_(NSMakeRect(*frame), False)
    control.addItemsWithTitles_(list(items))
    control.setFont_(A.NSFont.systemFontOfSize_(14))
    if owner:
        control.setTarget_(owner)
        control.setAction_(action)
    parent.addSubview_(control)
    return control


def show_window(window):
    window.makeKeyAndOrderFront_(None)
    window.makeMainWindow()
    A.NSApplication.sharedApplication().activateIgnoringOtherApps_(True)


class SettingsScreen:
    def __init__(self, owner):
        self.owner = owner
        screen = A.NSScreen.mainScreen().visibleFrame()
        scale = min(1.0, (screen.size.height-110)/786, (screen.size.width-60)/960)
        height, width = 786*scale+58, 960*scale
        self.window = A.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, width, height), A.NSWindowStyleMaskTitled | A.NSWindowStyleMaskClosable,
            A.NSBackingStoreBuffered, False)
        self.window.setTitle_('狗头军师 · 设置')
        self.window.setReleasedWhenClosed_(False)
        self.window.setLevel_(A.NSFloatingWindowLevel)
        self.window.setAppearance_(A.NSAppearance.appearanceNamed_(A.NSAppearanceNameAqua))
        view = self.window.contentView()
        view.setWantsLayer_(True)
        view.layer().setBackgroundColor_(color(0xF2F1EC).CGColor())
        # Fit the full design to the available display. A fixed settings surface
        # avoids layer-backed NSScrollView redraw artifacts in PyObjC on macOS.
        doc = A.NSView.alloc().initWithFrame_(NSMakeRect(0, 58, width, height-58))
        doc.setBounds_(NSMakeRect(0, 0, 960, 786))
        view.addSubview_(doc)
        label(doc, '设置', (24, 735, 700, 40), 30, True)
        label(doc, '让建议贴合你的关系、目标和说话方式', (25, 704, 800, 25), 14, tint=MUTED)
        route = card(doc, 24, 424, 438, 264, '接口与模型')
        label(route, '策略判断', (20, 163, 96, 25), 14)
        self.strategy = label(route, '', (117, 149, 300, 48), 14)
        label(route, '回复生成', (20, 110, 96, 25), 14)
        self.model = field(route, '', (117, 108, 298, 30))
        self.route = label(route, '', (20, 68, 395, 30), 11, tint=MUTED)
        self.key_status = label(route, '', (20, 19, 148, 35), 11, tint=MUTED)
        self.provider_button = button(route, owner, '配置接口', 'configureProviders:', (175, 21, 109, 35))
        self.provider_button.setEnabled_(not owner.demo)
        self.test_button = button(route, owner, '连通测试', 'testConnection:', (298, 21, 116, 35))
        relationship = card(doc, 478, 424, 438, 264, '当前会话 · 关系与目标')
        label(relationship, '对象', (20, 182, 50, 25), 14)
        self.subject = popup(relationship, ['当前会话'], (68, 179, 348, 30), owner, 'selectSubject:')
        label(relationship, '阶段', (20, 139, 42, 24), 13)
        self.stage = popup(relationship, STAGES, (65, 135, 135, 30))
        label(relationship, '目标', (217, 139, 42, 24), 13)
        self.goal = popup(relationship, GOALS, (260, 135, 155, 30))
        self.background = field(relationship, '', (20, 59, 396, 66))
        self.background.cell().setWraps_(True)
        self.background.setPlaceholderString_('补充背景：最近发生了什么？（最多 200 字）')
        button(relationship, owner, '完善双方资料', 'editProfile:', (274, 14, 141, 30))
        label(relationship, '不同对象分别设置', (20, 16, 230, 24), 11, tint=MUTED)
        reply = card(doc, 24, 113, 438, 295, '回复偏好')
        self.tone = A.NSSegmentedControl.alloc().initWithFrame_(NSMakeRect(20, 205, 395, 34))
        self.tone.setSegmentCount_(3)
        for index, tone in enumerate(TONES):
            self.tone.setLabel_forSegment_(tone, index)
            self.tone.setWidth_forSegment_(130, index)
        self.tone.setSelectedSegment_(0)
        reply.addSubview_(self.tone)
        label(reply, '回复长度', (20, 155, 100, 25), 14)
        self.length = popup(reply, LENGTHS, (122, 153, 188, 30))
        label(reply, '候选数量', (20, 110, 100, 25), 14)
        self.count = popup(reply, ['最多 1 条', '最多 2 条', '最多 3 条'], (122, 108, 188, 30))
        label(reply, '主策略由军师结合对话判断', (20, 68, 396, 26), 12, tint=MUTED)
        label(reply, '事实 · 推测 · 未知 · 下一步 · 停止条件', (20, 20, 396, 28), 13)
        reading = card(doc, 478, 113, 438, 295, '读屏与悬浮窗')
        label(reading, '识别方式', (20, 211, 95, 24), 14)
        self.ocr_method = popup(reading, ('Apple Vision · 本地', 'DeepSeek · 图片识别'),
                                (121, 207, 295, 32), owner, 'ocrMethodChanged:')
        self.ocr_note = label(reading, '本地识别；截图不发送至 OCR 服务', (20, 194, 396, 13), 10, tint=MUTED)
        self.auto = A.NSButton.alloc().initWithFrame_(NSMakeRect(20, 164, 396, 30))
        self.auto.setButtonType_(A.NSSwitchButton)
        self.auto.setTitle_('新消息自动分析')
        reading.addSubview_(self.auto)
        label(reading, '开启后，所选会话发往配置的分析服务', (20, 136, 396, 27), 11, tint=MUTED)
        self.scope = label(reading, '作用范围：尚未选定会话', (20, 100, 396, 31), 12)
        self.opacity_label = label(reading, '悬浮窗不透明度：92%', (20, 70, 396, 25), 14, True)
        self.opacity = A.NSSlider.alloc().initWithFrame_(NSMakeRect(20, 38, 396, 25))
        self.opacity.setMinValue_(55)
        self.opacity.setMaxValue_(100)
        self.opacity.setTarget_(owner)
        self.opacity.setAction_('opacityChanged:')
        self.opacity.setContinuous_(True)
        reading.addSubview_(self.opacity)
        label(reading, '只填入草稿，发送由你决定', (20, 8, 396, 24), 11, tint=MUTED)
        memory = card(doc, 24, 10, 892, 87, '关系档案（可选）')
        self.memory_status = label(memory, '未启用 · 不保存整份聊天', (20, 10, 430, 25), 12, tint=MUTED)
        self.memory_button = button(memory, owner, '启用档案', 'toggleMemory:', (470, 28, 125, 34))
        button(memory, owner, '查看与管理', 'manageMemory:', (610, 28, 135, 34))
        button(memory, owner, '撤销上次', 'undoMemory:', (760, 28, 110, 34))
        self.status = label(view, '', (24*scale, 8, 590*scale, 42), 11, tint=MUTED)
        button(view, owner, '取消', 'cancelSettings:', (656*scale, 12, 112*scale, 36))
        button(view, owner, '保存设置', 'saveSettings:', (783*scale, 12, 153*scale, 36), True)
        self.document = doc
        self.window.center()

    def refresh_subjects(self):
        self.subject_ids = list(self.owner.conversations.profiles)
        self.subject.removeAllItems()
        for index, identity in enumerate(self.subject_ids):
            self.subject.addItemWithTitle_(f"{index+1}. {self.owner.conversations.profiles[identity]['label']}")
        self.subject.selectItemAtIndex_(self.subject_ids.index(self.owner.conversations.current['id']))

    def refresh_profile(self):
        profile = self.owner.conversations.current
        self.stage.selectItemWithTitle_(profile['stage'])
        self.goal.selectItemWithTitle_(profile['goal'])
        self.background.setStringValue_(profile['background'])

    def refresh_memory(self):
        if self.owner.demo:
            self.memory_status.setStringValue_('离线演示 · 不访问档案')
            self.memory_button.setEnabled_(False)
            return
        try:
            state = self.owner.memory.call('status')
            text = '已暂停' if state.get('paused') else ('已启用' if state.get('consent_enabled') else '未启用')
            self.memory_status.setStringValue_(text + ' · 不保存整份聊天')
            self.memory_button.setTitle_('恢复档案' if state.get('paused') else ('暂停档案' if state.get('consent_enabled') else '启用档案'))
        except ValueError as error:
            self.memory_status.setStringValue_(str(error))

    def show(self):
        self.refresh_provider_summary(reset_model=True)
        self.refresh_subjects()
        self.refresh_profile()
        self.refresh_memory()
        options = self.owner.reply_options
        self.tone.setSelectedSegment_(TONES.index(options.tone))
        self.length.selectItemWithTitle_(options.length)
        self.count.selectItemAtIndex_(options.count-1)
        self.ocr_method.selectItemAtIndex_(0 if self.owner.ocr_method == 'vision' else 1)
        self.owner.ocrMethodChanged_(self.ocr_method)
        self.opacity.setDoubleValue_(self.owner.opacity_value)
        self.opacity_label.setStringValue_(f'悬浮窗不透明度：{self.owner.opacity_value:.0f}%')
        self.auto.setState_(int(self.owner.auto_gate.enabled))
        self.auto.setEnabled_(not self.owner.demo)
        key = self.owner.conversations.current_key
        self.scope.setStringValue_('作用范围：' + (key[1] if key else '请先读取并核对会话'))
        self.window.setTitle_('狗头军师 · 设置')
        self.document.setNeedsDisplay_(True)
        show_window(self.window)

    def refresh_provider_summary(self, reset_model=False):
        if self.owner.demo:
            self.model.setStringValue_('deepseek-flash')
            self.strategy.setStringValue_('TypeSafe · Jev 1.13.0\n离线演示')
            self.key_status.setStringValue_('离线演示')
            self.route.setStringValue_('合成示例，不调用模型接口')
            return
        self.strategy.setStringValue_(
            'TypeSafe · ' + self.owner.jev_config.model if self.owner.jev_config else
            (self.owner.jev_error or '由回复模型选策略'))
        try:
            config = self.owner.reply_config()
            if reset_model or not str(self.model.stringValue()).strip():
                self.model.setStringValue_(config.model)
            self.key_status.setStringValue_('回复密钥已配置' if config.key else '本机服务免密钥')
            self.route.setStringValue_(config.base)
        except ValueError as error:
            self.key_status.setStringValue_('回复接口待配置')
            self.route.setStringValue_(str(error))


class ProviderSettingsScreen:
    """Two masked Keychain inputs; existing secrets are never placed in fields."""

    def __init__(self, owner):
        self.owner = owner
        width, height = 650, 520
        self.window = A.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, width, height), A.NSWindowStyleMaskTitled | A.NSWindowStyleMaskClosable,
            A.NSBackingStoreBuffered, False)
        self.window.setTitle_('狗头军师 · 接口配置')
        self.window.setReleasedWhenClosed_(False)
        self.window.setLevel_(A.NSFloatingWindowLevel)
        self.window.setAppearance_(A.NSAppearance.appearanceNamed_(A.NSAppearanceNameAqua))
        view = self.window.contentView()
        view.setWantsLayer_(True)
        view.layer().setBackgroundColor_(color(0xF2F1EC).CGColor())
        label(view, '接口配置', (28, 467, 570, 36), 26, True)
        label(view, '在这里直接保存密钥到 Mac 钥匙串；不会写进项目文件。',
              (28, 437, 580, 23), 13, tint=MUTED)

        deepseek = card(view, 24, 269, 602, 155, 'DeepSeek · 回复生成 / 可选图片识别')
        label(deepseek, '官方接口 api.deepseek.com · 回复模型在主设置页选择',
              (20, 87, 560, 22), 12, tint=MUTED)
        self.deepseek_key = secure_field(deepseek, (20, 45, 350, 32))
        button(deepseek, owner, '保存 Key', 'saveDeepSeekKey:', (380, 45, 95, 32), True)
        button(deepseek, owner, '移除', 'removeDeepSeekKey:', (485, 45, 92, 32))
        self.deepseek_status = label(deepseek, '', (20, 12, 560, 27), 12, tint=MUTED)

        jev = card(view, 24, 95, 602, 155, 'TypeSafe · Jev 策略判断（可选）')
        label(jev, '官方接口 api.typesafe.ai · 当前模型 jev-1.13.0',
              (20, 87, 560, 22), 12, tint=MUTED)
        self.jev_key = secure_field(jev, (20, 45, 350, 32))
        button(jev, owner, '保存 Key', 'saveJevKey:', (380, 45, 95, 32), True)
        button(jev, owner, '移除', 'removeJevKey:', (485, 45, 92, 32))
        self.jev_status = label(jev, '', (20, 12, 560, 27), 12, tint=MUTED)

        self.status = label(view, '保存后可点“连通测试”；测试会调用接口并产生少量用量。',
                            (28, 22, 425, 48), 11, tint=MUTED)
        button(view, owner, '连通测试', 'testConnection:', (451, 29, 98, 36))
        button(view, owner, '关闭', 'closeProviderSettings:', (558, 29, 68, 36))
        self.window.center()

    def refresh_status(self):
        if self.owner.demo:
            self.deepseek_status.setStringValue_('离线演示 · 不访问钥匙串')
            self.jev_status.setStringValue_('离线演示 · 不访问钥匙串')
            return
        try:
            stored = bool(read_deepseek_keychain())
            override = any(name in os.environ for name in
                           ('GOUTOU_API_BASE', 'GOUTOU_MODEL', 'GOUTOU_API_KEY'))
            self.deepseek_status.setStringValue_(
                ('钥匙串已保存' if stored else '钥匙串未配置') +
                (' · 当前环境变量优先；仅官方 DeepSeek 路由可用此 Key' if override else ' · 可直接用于官方接口'))
        except ValueError as error:
            self.deepseek_status.setStringValue_(str(error))
        try:
            stored = bool(read_jev_keychain())
            suffix = (' · 环境变量已关闭 Jev' if os.environ.get('GOUTOU_JEV_ENABLED') == '0'
                      else ' · 当前环境变量 Key 优先' if os.environ.get('GOUTOU_JEV_API_KEY')
                      else ' · 保存后自动启用策略层')
            self.jev_status.setStringValue_(('钥匙串已保存' if stored else '钥匙串未配置') + suffix)
        except ValueError as error:
            self.jev_status.setStringValue_(str(error))

    def show(self):
        self.deepseek_key.setStringValue_('')
        self.jev_key.setStringValue_('')
        self.refresh_status()
        show_window(self.window)


class ProfileEditor:
    def __init__(self, owner):
        self.window = A.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 490, 440), A.NSWindowStyleMaskTitled | A.NSWindowStyleMaskClosable,
            A.NSBackingStoreBuffered, False)
        self.window.setTitle_('完善双方资料 · 不知道可留空')
        self.window.setReleasedWhenClosed_(False)
        self.window.setLevel_(A.NSFloatingWindowLevel)
        self.window.setAppearance_(A.NSAppearance.appearanceNamed_(A.NSAppearanceNameAqua))
        self.fields = {}
        view = self.window.contentView()
        labels = [('label', '对象称呼'), ('my_mbti', '我的 MBTI'), ('their_mbti', '对方 MBTI'),
                  ('my_score', '我的主观综合评分 0–100'), ('their_score', '对方主观综合评分 0–100'), ('notes', '优势、短板或关键背景')]
        for index, (key, title) in enumerate(labels):
            y = 380-index*51
            label(view, title, (20, y, 216, 28), 13)
            self.fields[key] = field(view, owner.conversations.current[key], (240, y, 229, 30))
        label(view, '评分仅代表你的主观评价，不作为人格或关系事实。', (20, 78, 450, 30), 12, tint=MUTED)
        button(view, owner, '应用到本轮', 'saveProfile:', (284, 26, 184, 36), True)
        self.status = label(view, '', (20, 20, 250, 50), 11, tint=MUTED)
        self.window.center()
        show_window(self.window)
