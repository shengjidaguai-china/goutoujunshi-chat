"""Optional native Mac companion. Run --demo for a synthetic, offline UI preview."""
from __future__ import annotations

import queue
import sys
import threading
import time
from dataclasses import replace
from pathlib import Path

import AppKit as A
import objc
from Foundation import NSObject, NSTimer, NSMakeRect

from overlay import ReplyOverlay
from client import Config
from jev import JevConfig
from pipeline import analyze_snapshot, rewrite_snapshot
from ranking import EXPLANATION, apply_scores
from core import Session, Snapshot, build_messages, parse_advice
from settings_ui import SettingsScreen, ProviderSettingsScreen, ProfileEditor
from credentials import save_key, delete_key
from detail_ui import AnalysisScreen
from trend_ui import TrendWindow
from trend import load_csv, load_demo
from experience import Conversations, AutoGate, ReplyPreferences, TONES, GOALS, profile_context, validate_profile, empty_profile
from memory_bridge import MemoryBridge
import preferences


DEMO_TRANSCRIPT = "我：这周六要不要一起去看展？\n对方：这周有点忙，下周再看看吧。"
DEMO_ADVICE = {
    "intent": "可能想先缓一缓，暂时不确定见面时间。",
    "intent_confidence": 0.62,
    "support": "有期待又拿不准对方的意思很正常，先不用把这句话判成拒绝。",
    "facts": ["你提出了周六看展，对方表示这周忙。", "对方提到下周，但没有确认时间。"],
    "hypotheses": ["可能确实忙，也可能尚未决定是否赴约。"],
    "unknowns": ["此前是否有主动联系或兑现邀约的表现。"],
    "strategy": "降压", "recommendation": "先接住安排，这轮不追问具体时间。",
    "next_step": "下周有合适安排时可以再邀请一次，观察是否提供具体时间。",
    "stop_condition": "如果明确表示不想见面，停止推进；若持续含糊，降低投入。",
    "candidates": [
        {"text": "好，你先忙，下周有空再聊。", "reason": "接住安排，减少压力。", "tradeoff": "本轮不会立刻确认见面。"},
        {"text": "行，那这周先不安排啦。", "reason": "简短确认，保留自己的节奏。", "tradeoff": "表达更克制。"},
        {"text": "没问题，等你空下来再约。", "reason": "尊重对方时间。", "tradeoff": "下一次联系时间仍不确定。"},
    ], "question": "",
}


class Controller(NSObject):
    def init(self):
        self = objc.super(Controller, self).init()
        if self is None:
            return None
        self.demo = "--demo" in sys.argv
        self.saved_preferences = preferences.load()
        self.ocr_method = self.saved_preferences.get('ocr_method', 'vision')
        self.reply_model_override = self.saved_preferences.get("model", "")
        self.opacity_value = self.saved_preferences.get("opacity", 92.0)
        self.settings_screen = None
        self.provider_settings = None
        self.profile_editor = None
        self.trend_window = None
        self.conversations = Conversations()
        self.auto_gate = AutoGate()
        self.reply_options = ReplyPreferences(**self.saved_preferences.get('reply', {}))
        self.memory = MemoryBridge()
        self.jev_config = None
        self.jev_error = None
        if not self.demo:
            try:
                self.jev_config = JevConfig.optional()
            except ValueError as error:
                self.jev_error = str(error)
        self.session = Session()
        self.events = queue.Queue()
        self.captured = None
        self.result_inputs = None
        self.busy = False
        self.candidate_buttons = []
        self.next_capture = 0.0
        self.auto_reading = False
        self.result_capture = None
        self.detail_screen = AnalysisScreen(self)
        self.window = self.detail_screen.window
        if self.demo:
            self.transcript.setString_(DEMO_TRANSCRIPT)
            self.title_field.setStringValue_("演示对象 A")
            self.conversations.current['stage'] = '了解中'
            self.confirm.setState_(A.NSControlStateValueOn)
            self.route.setStringValue_("离线合成示例 · 不读微信 · 不调用模型 · 不回填")
        else:
            try:
                config = self.reply_config()
                strategy = f"策略：TypeSafe {self.jev_config.model}；" if self.jev_config else ""
                self.route.setStringValue_(strategy + f"回复：{config.model} · {config.base}")
            except ValueError as error:
                prefix = f"策略：TypeSafe {self.jev_config.model}；" if self.jev_config else ""
                self.route.setStringValue_(prefix + str(error))
            if self.jev_error:
                self.route.setStringValue_(self.jev_error)
            self.route.setToolTip_(self.route.stringValue())
        self.window.center()
        self.build_panel()
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            .15, self, "poll:", None, True)
        return self

    @objc.python_method
    def build_panel(self):
        self.overlay = ReplyOverlay(self)
        self.overlay.surface.opacity = self.opacity_value / 100
        self.panel = self.overlay.panel
        self.sync_panel()
        if self.demo:
            self.analyze_(None)

    def toggleOverlay_(self, sender):
        if self.panel.isVisible():
            self.panel.orderOut_(None)
        else:
            self.overlay.position_panel()
            self.panel.makeKeyAndOrderFront_(None)

    def collapseOverlay_(self, sender):
        self.panel.orderOut_(None)

    def refreshOverlay_(self, sender):
        if self.busy:
            return
        self.overlay.reviewing = False
        self.overlay.last_content = None
        if self.demo or (self.captured is None and self.transcript.string()):
            self.analyze_(None)
        else:
            self.capture_(None)

    def quit_(self, sender):
        self.session.replace(None)
        self.timer.invalidate()
        A.NSApplication.sharedApplication().terminate_(None)

    def details_(self, sender):
        self.detail_screen.show(0)

    def trend_(self, sender):
        if self.trend_window is None:
            self.trend_window = TrendWindow(self)
        self.trend_window.show()

    def selectTrendCase_(self, sender):
        if sender.indexOfSelectedItem() == 0:
            self.trend_window.reset()
            return
        try:
            self.trend_window.set_trend(load_demo(
                self.trend_window.case_ids[sender.indexOfSelectedItem()-1]))
        except (ValueError, IndexError, OSError) as error:
            self.trend_window.summary.setStringValue_(str(error))

    def importTrend_(self, sender):
        panel = A.NSOpenPanel.openPanel()
        panel.setCanChooseFiles_(True)
        panel.setCanChooseDirectories_(False)
        panel.setAllowsMultipleSelection_(False)
        panel.setAllowedFileTypes_(['csv'])
        if panel.runModal() != A.NSModalResponseOK:
            return
        try:
            filename = str(panel.URL().path())
            self.trend_window.case_popup.selectItemAtIndex_(0)
            self.trend_window.set_trend(load_csv(filename, '导入记录 · ' + Path(filename).stem))
        except (ValueError, OSError) as error:
            self.trend_window.summary.setStringValue_(str(error))

    def detailTab_(self, sender):
        self.detail_screen.select_tab(sender.selectedSegment())

    def detailAnalyze_(self, sender):
        if self.detail_screen.tabs.selectedSegment() == 1:
            self.analyze_(sender)
        else:
            self.refreshOverlay_(sender)

    def rankingInfo_(self, sender):
        alert = A.NSAlert.alloc().init()
        alert.setMessageText_('候选回复排序')
        alert.setInformativeText_(EXPLANATION + '\n根据当前对话、关系目标、用户口吻和表达代价评分。只有一个候选时，100% 仅表示它是唯一候选。' +
                                  ('\n当前为离线演示，数字是示例。' if self.demo else ''))
        alert.addButtonWithTitle_('知道了')
        alert.runModal()

    def toggleReason_(self, sender):
        self.overlay.toggle_reason(sender.tag())

    def rewriteReplies_(self, sender):
        if self.busy or not self.session.advice or not self.session.advice['candidates']:
            return
        if self.inputs() != self.result_inputs:
            self.status.setStringValue_('对话或背景已变化，请重新分析')
            return
        previous = self.session.advice
        inputs = self.result_inputs
        snapshot = self.session.snapshot
        options = self.reply_options
        try:
            config = None if self.demo else self.reply_config()
        except ValueError as error:
            self.status.setStringValue_(str(error))
            return
        self.session.revision += 1
        revision = self.session.revision
        self.busy = True
        self.status.setStringValue_('正在调整口吻并重新排序 · 保留本轮判断与策略…')
        def rewrite():
            if self.demo:
                import copy
                result = copy.deepcopy(previous)
                for row, text in zip(result['candidates'], ('好，你先忙', '行，那等你有空再说', '好，下周再看')):
                    row['text'] = text
                return result
            return rewrite_snapshot(snapshot, inputs[2], inputs[3], config, previous, options)
        def done(result, error):
            self.busy = False
            if revision != self.session.revision or self.inputs() != inputs:
                self.status.setStringValue_('输入已变化，旧改写已丢弃')
                return
            if error:
                self.status.setStringValue_(error + '；原候选已保留')
                return
            self.session.accept(revision, result)
            self.status.setStringValue_('口吻已调整' + (' · 排序暂不可用' if result.get('ranking_status') == 'unavailable' else ' · 请自行选择采用'))
            self.sync_panel()
        self.work(rewrite, done)

    def settings_(self, sender):
        if not self.demo:
            try:
                for identity, name in self.memory.list_profiles():
                    if identity not in self.conversations.profiles:
                        profile = empty_profile(name)
                        profile.update(id=identity, archived=True)
                        self.conversations.profiles[identity] = profile
            except ValueError as error:
                self.status.setStringValue_(str(error))
        if self.settings_screen is None:
            self.settings_screen = SettingsScreen(self)
        self.settings_screen.show()

    @objc.python_method
    def reply_config(self):
        config = Config.from_env()
        return replace(config, model=self.reply_model_override) if (
            self.reply_model_override and self.saved_preferences.get("base") == config.base) else config

    def opacityChanged_(self, sender):
        value = float(sender.doubleValue())
        self.overlay.surface.opacity = value / 100
        self.overlay.surface.setNeedsDisplay_(True)
        self.settings_screen.opacity_label.setStringValue_(f"悬浮窗不透明度：{value:.0f}%")

    def ocrMethodChanged_(self, sender):
        cloud = sender.indexOfSelectedItem() == 1
        self.settings_screen.ocr_note.setStringValue_(
            '聊天区域截图发往 DeepSeek · 按图片计费' if cloud else '本地识别；截图不发送至 OCR 服务')
        self.settings_screen.auto.setToolTip_(
            '开启后每次画面变化可能上传截图并产生费用' if cloud else '自动读取所选会话的可见文字')

    def cancelSettings_(self, sender):
        self.overlay.surface.opacity = self.opacity_value / 100
        self.overlay.surface.setNeedsDisplay_(True)
        self.settings_screen.window.orderOut_(None)

    def configureProviders_(self, sender):
        if self.demo:
            self.settings_screen.status.setStringValue_('离线演示不读取或保存密钥，请正式启动后配置')
            return
        if self.busy:
            self.settings_screen.status.setStringValue_('请等待当前操作完成再配置接口')
            return
        if self.provider_settings is None:
            self.provider_settings = ProviderSettingsScreen(self)
        self.provider_settings.show()

    def closeProviderSettings_(self, sender):
        if self.provider_settings is not None:
            self.provider_settings.deepseek_key.setStringValue_('')
            self.provider_settings.jev_key.setStringValue_('')
            self.provider_settings.window.orderOut_(None)

    @objc.python_method
    def reload_providers(self):
        self.jev_config = None
        self.jev_error = None
        try:
            self.jev_config = JevConfig.optional()
        except ValueError as error:
            self.jev_error = str(error)
        try:
            config = self.reply_config()
            prefix = f'策略：TypeSafe {self.jev_config.model}；' if self.jev_config else ''
            self.route.setStringValue_(prefix + f'回复：{config.model} · {config.base}')
        except ValueError as error:
            self.route.setStringValue_(str(error))
        if self.jev_error:
            self.route.setStringValue_(self.jev_error)
        self.route.setToolTip_(self.route.stringValue())
        if self.settings_screen is not None:
            self.settings_screen.refresh_provider_summary()
        if self.provider_settings is not None:
            self.provider_settings.refresh_status()

    @objc.python_method
    def store_provider_key(self, provider, control):
        if self.demo or self.busy:
            self.provider_settings.status.setStringValue_('离线演示或当前操作进行中，不能修改密钥')
            return
        value = str(control.stringValue())
        try:
            save_key(provider, value)
            control.setStringValue_('')
            self.reload_providers()
            name = 'DeepSeek' if provider == 'deepseek' else 'Jev'
            self.provider_settings.status.setStringValue_(
                f'{name} Key 已保存到 Mac 钥匙串；可点“连通测试”验证接口。')
        except ValueError as error:
            self.provider_settings.status.setStringValue_(str(error))

    def saveDeepSeekKey_(self, sender):
        self.store_provider_key('deepseek', self.provider_settings.deepseek_key)

    def saveJevKey_(self, sender):
        self.store_provider_key('jev', self.provider_settings.jev_key)

    @objc.python_method
    def remove_provider_key(self, provider):
        if self.demo or self.busy:
            self.provider_settings.status.setStringValue_('离线演示或当前操作进行中，不能修改密钥')
            return
        name = 'DeepSeek' if provider == 'deepseek' else 'Jev'
        if not self.ask(f'移除{name}密钥？', '只删除本项目专用的 Mac 钥匙串条目。环境变量配置不会改变。', '移除'):
            return
        try:
            delete_key(provider)
            self.reload_providers()
            self.provider_settings.status.setStringValue_(f'{name} 钥匙串密钥已移除')
        except ValueError as error:
            self.provider_settings.status.setStringValue_(str(error))

    def removeDeepSeekKey_(self, sender):
        self.remove_provider_key('deepseek')

    def removeJevKey_(self, sender):
        self.remove_provider_key('jev')

    @objc.python_method
    def ask(self, title, message, accept):
        alert = A.NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(message)
        alert.addButtonWithTitle_('取消')
        alert.addButtonWithTitle_(accept)
        return alert.runModal() == A.NSAlertSecondButtonReturn

    def saveSettings_(self, sender):
        if self.busy:
            self.settings_screen.status.setStringValue_('请等待当前操作完成再保存')
            return
        ui = self.settings_screen
        try:
            ocr_method = preferences.OCR_METHODS[ui.ocr_method.indexOfSelectedItem()]
            if ocr_method == 'deepseek' and not self.demo:
                from cloud_ocr import deepseek_config
                deepseek_config()
            model = str(ui.model.stringValue()).strip()
            if not model or len(model) > 160:
                raise ValueError('请填写有效的模型名')
            options = ReplyPreferences(TONES[ui.tone.selectedSegment()], str(ui.length.titleOfSelectedItem()), ui.count.indexOfSelectedItem()+1)
            profile = dict(self.conversations.current)
            profile.update(stage=str(ui.stage.titleOfSelectedItem()), goal=str(ui.goal.titleOfSelectedItem()), background=str(ui.background.stringValue()))
            validate_profile(profile)
            auto = bool(ui.auto.state()) and not self.demo
            key = self.conversations.current_key
            if auto and (key is None or not self.confirm.state()):
                raise ValueError('请先读取并确认当前会话的文字和说话人，再开启自动分析')
            config = Config('https://api.deepseek.com', model, '') if self.demo else self.reply_config()
            if auto and (not self.auto_gate.enabled or key not in self.auto_gate.allowed
                         or (ocr_method == 'deepseek' and self.ocr_method != 'deepseek')):
                image_note = 'DeepSeek OCR 还会上传聊天区域截图；' if ocr_method == 'deepseek' else ''
                if not self.ask('开启当前会话自动分析？', f'仅对“{key[1]}”生效。{image_note}稳定的新对方消息及关系背景将发送到 TypeSafe（如已启用）和 {config.base}，可能产生 API 用量。不会自动填入或发送；重启后关闭。', '开启'):
                    return
            opacity = float(ui.opacity.doubleValue())
            if not self.demo:
                preferences.save(model, config.base, opacity, reply=options, ocr_method=ocr_method)
            self.conversations.update(profile)
            self.reply_options = options
            self.saved_preferences = dict(model=model, base=config.base, opacity=opacity,
                                          ocr_method=ocr_method)
            self.reply_model_override, self.opacity_value = model, opacity
            self.ocr_method = ocr_method
            self.background.setStringValue_(profile['background'])
            self.scene.selectItemWithTitle_(GOALS[profile['goal']])
            self.auto_gate.configure(auto, key, self.captured.identity if self.captured else None)
            self.overlay.reviewing = False
            self.overlay.last_content = None
            self.auto_reading = auto
            self.auto_read.setState_(int(auto))
            self.next_capture = 0
            self.reset_result()
            saved = self.memory.save_profile(profile) if not self.demo else 0
            ui.status.setStringValue_('设置已保存' + (f' · 档案更新 {saved} 项，可撤销上次保存' if saved else ' · 本轮资料未写入档案'))
            self.route.setStringValue_(f'回复：{model} · {config.base}')
            ui.refresh_memory()
        except (ValueError, IndexError) as error:
            ui.status.setStringValue_(str(error))

    def selectSubject_(self, sender):
        if self.busy:
            self.settings_screen.refresh_subjects()
            return
        identity = self.settings_screen.subject_ids[sender.indexOfSelectedItem()]
        try:
            if self.conversations.profiles[identity].get('archived'):
                self.conversations.profiles[identity] = self.memory.load_profile(identity)
            self.conversations.bind(identity)
        except ValueError as error:
            self.settings_screen.status.setStringValue_(str(error))
            self.settings_screen.refresh_subjects()
            return
        self.background.setStringValue_(self.conversations.current['background'])
        self.scene.selectItemWithTitle_(GOALS[self.conversations.current['goal']])
        self.auto_gate.configure(False, None)
        self.auto_reading = False
        self.auto_read.setState_(0)
        self.reset_result()
        if self.trend_window:
            self.trend_window.reset()
        self.confirm.setState_(0)
        self.settings_screen.refresh_profile()
        self.settings_screen.auto.setState_(0)
        self.settings_screen.status.setStringValue_('对象已绑定当前会话；请重新核对后分析')

    def editProfile_(self, sender):
        if self.busy:
            return
        if self.profile_editor:
            self.profile_editor.window.orderOut_(None)
        self.profile_editor = ProfileEditor(self)
        self.profile_editor.subject_id = self.conversations.current['id']

    def saveProfile_(self, sender):
        if self.busy:
            return
        try:
            if self.profile_editor.subject_id != self.conversations.current['id']:
                raise ValueError('对象已变化，请重新打开资料页')
            profile = dict(self.conversations.current)
            profile.update({key: str(value.stringValue()).strip() for key, value in self.profile_editor.fields.items()})
            self.conversations.update(profile)
            self.reset_result()
            self.profile_editor.window.orderOut_(None)
            self.settings_screen.refresh_subjects()
            self.settings_screen.status.setStringValue_('资料已用于本轮；点击保存设置可更新已启用的档案')
        except ValueError as error:
            self.profile_editor.status.setStringValue_(str(error))

    def toggleMemory_(self, sender):
        if self.demo or self.busy:
            return
        try:
            state = self.memory.call('status')
            if not state.get('consent_enabled'):
                if not self.ask('启用本地关系档案？', '允许狗头军师保存你填写的精简对象资料。之后保存设置时更新，可查看、暂停、撤销或删除。不保存整份聊天。', '同意启用'):
                    return
                self.memory.call('enable', '--confirm')
            else:
                self.memory.call('resume' if state.get('paused') else 'pause')
            self.settings_screen.refresh_memory()
            self.settings_screen.status.setStringValue_('档案状态已更新；点击保存设置才保存当前资料')
        except ValueError as error:
            self.settings_screen.status.setStringValue_(str(error))

    def undoMemory_(self, sender):
        if self.demo or self.busy:
            return
        try:
            self.memory.undo_save()
            self.settings_screen.status.setStringValue_('已撤销上次档案保存；当前本轮编辑仍保留')
        except ValueError as error:
            self.settings_screen.status.setStringValue_(str(error))

    def manageMemory_(self, sender):
        if self.demo or self.busy:
            return
        try:
            state = self.memory.call('status')
            if not state.get('exists'):
                raise ValueError('尚未创建档案')
            identity = self.conversations.current['id']
            rows = self.memory.call('show', '--subject-id', identity)['memories']
            names = dict(display_label='对象称呼', stage='关系阶段', goal='当前目标', background='补充背景',
                         my_mbti='我的 MBTI', their_mbti='对方 MBTI', my_score='我的主观综合评分',
                         their_score='对方主观综合评分', notes='关键背景')
            summary = '\n'.join(f"{names.get(row['field'], row['field'])}：{row['value']}" for row in rows if row['subject_id'] == identity) or '当前对象尚无已保存资料'
            alert = A.NSAlert.alloc().init()
            alert.setMessageText_('当前对象档案 · ' + self.conversations.current['label'])
            alert.setInformativeText_(summary)
            for title in ('关闭', '删除当前对象', '撤回保存同意'):
                alert.addButtonWithTitle_(title)
            answer = alert.runModal()
            if answer == A.NSAlertSecondButtonReturn and self.ask('永久删除当前对象档案？', '将删除此对象的资料及相关撤销记录，无法恢复。', '确认删除'):
                self.memory.call('forget-object', identity, '--confirm')
                self.memory.last_operations = []
            elif answer == A.NSAlertThirdButtonReturn:
                self.memory.call('revoke', '--confirm')
            self.settings_screen.refresh_memory()
        except ValueError as error:
            self.settings_screen.status.setStringValue_(str(error))

    def testConnection_(self, sender):
        def show_status(message):
            self.settings_screen.status.setStringValue_(message)
            if self.provider_settings is not None and self.provider_settings.window.isVisible():
                self.provider_settings.status.setStringValue_(message)

        if self.busy:
            return
        if self.demo:
            show_status("离线演示不调用接口，请在正式运行时测试")
            return
        try:
            if self.jev_error:
                raise ValueError(self.jev_error)
            config = replace(self.reply_config(), model=str(self.settings_screen.model.stringValue()).strip())
            if not config.model:
                raise ValueError("请填写模型名")
        except ValueError as error:
            show_status(str(error))
            return
        self.busy = True
        self.settings_screen.test_button.setEnabled_(False)
        show_status("使用合成对话测试，会产生少量 API 用量…")
        def test():
            return analyze_snapshot(Snapshot("连通测试", DEMO_TRANSCRIPT), "邀约推进", "合成测试", config, self.jev_config)
        def done(result, error):
            self.busy = False
            self.settings_screen.test_button.setEnabled_(True)
            show_status(error or f"连通成功 · {config.model} · 返回 {len(result['candidates'])} 条候选")
        self.work(test, done)

    def confirmOverlay_(self, sender):
        if self.busy:
            return
        self.transcript.setString_(self.overlay.review_text.string())
        self.confirm.setState_(A.NSControlStateValueOn)
        self.overlay.reviewing = False
        self.overlay.last_content = None
        self.analyze_(None)

    def autoRead_(self, sender):
        if bool(sender.state()) and self.ocr_method == 'deepseek' and not self.ask(
                '开启 DeepSeek 自动读屏？',
                '聊天区域截图会在画面变化时上传至 DeepSeek，并产生图片 API 用量。', '开启'):
            sender.setState_(0)
            return
        self.auto_reading = bool(sender.state())
        if not self.auto_reading:
            self.auto_gate.configure(False, None)
        self.next_capture = 0
        self.status.setStringValue_("自动读屏已开启；内容变化后仍需核对并点击分析" if self.auto_reading else "自动读屏已暂停")

    @objc.python_method
    def sync_panel(self):
        self.overlay.sync(self.session.advice, str(self.status.stringValue()), self.busy)
        self.detail_screen.sync()

    @objc.python_method
    def accept_capture(self, snapshot):
        previous_key = self.conversations.current_key
        profile = self.conversations.select(snapshot)
        if previous_key != self.conversations.current_key:
            self.background.setStringValue_(profile['background'])
            self.scene.selectItemWithTitle_(GOALS[profile['goal']])
        self.captured = snapshot
        self.title_field.setStringValue_(snapshot.title)
        self.transcript.setString_(snapshot.transcript)

    @objc.python_method
    def read_in_background(self):
        self.busy = True
        self.next_capture = time.monotonic() + 2.0
        revision = self.session.revision
        def read():
            from adapter import capture
            return capture(method=self.ocr_method, reuse_unchanged=True)[0]
        def done(snapshot, error):
            self.busy = False
            if not self.auto_reading or revision != self.session.revision:
                return
            if error:
                self.auto_reading = False
                self.auto_gate.configure(False, None)
                self.auto_read.setState_(0)
                self.status.setStringValue_(error + '；自动读屏已暂停')
                return
            ready = self.auto_gate.ready(snapshot)
            unchanged = self.captured is not None and self.captured.identity == snapshot.identity
            if not unchanged:
                self.reset_result()
                self.accept_capture(snapshot)
                self.confirm.setState_(0)
            if ready:
                self.confirm.setState_(1)
                self.overlay.reviewing = False
                self.overlay.last_content = None
                self.analyze_(None)
            elif not unchanged:
                if self.auto_gate.enabled:
                    self.status.setStringValue_('对话已更新 · 等待选定会话的稳定对方消息')
                else:
                    self.status.setStringValue_('对话已更新 · 请核对文字后重新分析')
                    self.overlay.show_review(snapshot.transcript)
        self.work(read, done)

    @objc.python_method
    def inputs(self):
        profile = dict(self.conversations.current)
        profile['background'] = str(self.background.stringValue())
        return (str(self.title_field.stringValue()), str(self.transcript.string()),
                str(self.scene.titleOfSelectedItem()), profile_context(profile))

    @objc.python_method
    def reset_result(self):
        self.session.replace(None)
        self.result_inputs = None
        self.result_capture = None
        for button in self.candidate_buttons:
            button.setEnabled_(False)

    @objc.python_method
    def work(self, function, callback):
        def run():
            try:
                value, error = function(), None
            except ValueError as exc:
                value, error = None, str(exc)
            except Exception:
                value, error = None, "操作失败，请检查依赖和系统权限；未自动重试或发送"
            self.events.put((callback, value, error))
        threading.Thread(target=run, daemon=True).start()

    def capture_(self, sender):
        if self.busy:
            return
        previous = self.captured
        self.reset_result()
        self.confirm.setState_(A.NSControlStateValueOff)
        self.captured = None
        if self.demo:
            self.transcript.setString_(DEMO_TRANSCRIPT)
            self.status.setStringValue_("已载入合成示例，请确认后分析")
            self.detail_screen.show(1)
            return
        self.busy = True
        self.status.setStringValue_("正在读取微信窗口…" + ('聊天截图将发往 DeepSeek' if self.ocr_method == 'deepseek' else ''))
        revision = self.session.revision

        def read():
            from adapter import capture
            return capture(method=self.ocr_method)[0]

        def done(snapshot, error):
            self.busy = False
            if revision != self.session.revision:
                return
            if error:
                self.status.setStringValue_(error)
                return
            self.accept_capture(snapshot)
            self.status.setStringValue_("已读取；请核对双方归属和错字，再点击分析。")
            if self.window.isVisible():
                self.detail_screen.select_tab(1)
            else:
                self.overlay.show_review(snapshot.transcript)
        self.work(read, done)

    def analyze_(self, sender):
        if self.busy:
            return
        if not self.confirm.state():
            self.status.setStringValue_("请先核对并勾选上方确认项")
            self.detail_screen.show(1)
            return
        show_details = self.window.isVisible()
        inputs = self.inputs()
        title, transcript, scene, background = inputs
        try:
            if self.jev_error:
                raise ValueError(self.jev_error)
            captured = self.captured
            snapshot = Snapshot(title, transcript, captured.window_id if captured else 0,
                                captured.source if captured else "manual")
            config = None if self.demo else self.reply_config()
            messages, paths = build_messages(snapshot, scene, background)
        except ValueError as error:
            self.status.setStringValue_(str(error))
            return
        self.reset_result()
        revision = self.session.replace(snapshot)
        self.busy = True
        self.status.setStringValue_("正在分析意图、生成回复并评估候选排序…")

        options = self.reply_options
        def analyze():
            if self.demo:
                data = parse_advice(__import__('json').dumps(DEMO_ADVICE))
                data['candidates'] = data['candidates'][:options.count]
                import json
                data['candidates'] = apply_scores(data['candidates'], json.dumps({'scores': [
                    {'id': i, 'score': score} for i, score in enumerate((70, 25, 5)[:options.count])]}))
                data['ranking_status'] = 'demo'
                return data
            return analyze_snapshot(snapshot, scene, background, config, self.jev_config, options)

        def done(advice, error):
            self.busy = False
            if revision != self.session.revision or inputs != self.inputs():
                self.status.setStringValue_("输入已变化，旧分析已丢弃；请重新分析")
                return
            if error:
                self.status.setStringValue_(error)
                return
            self.session.accept(revision, advice)
            self.result_inputs = inputs
            self.result_capture = captured
            for i, button in enumerate(self.candidate_buttons):
                available = button.tag() < len(advice["candidates"])
                if i % 2:
                    available = (available and not self.demo and captured is not None
                                 and bool(captured.title) and title == captured.title)
                button.setEnabled_(available)
            self.status.setStringValue_("分析完成 · " + ('排序暂不可用，保留生成顺序' if advice.get('ranking_status') == 'unavailable'
                                                         else ('离线示例，权重为演示数字' if self.demo else '推荐权重不代表回复成功率')))
            self.sync_panel()
            if show_details:
                self.detail_screen.show(0)
            else:
                self.window.orderOut_(None)
        self.work(analyze, done)

    @objc.python_method
    def candidate(self, sender):
        if not self.session.advice or self.inputs() != self.result_inputs:
            raise ValueError("对话或背景已变化，请重新分析")
        return self.session.advice["candidates"][sender.tag()]["text"]

    def copyCandidate_(self, sender):
        try:
            text = self.candidate(sender)
            pasteboard = A.NSPasteboard.generalPasteboard()
            pasteboard.clearContents()
            pasteboard.setString_forType_(text, A.NSPasteboardTypeString)
            self.status.setStringValue_("已复制候选，请核对接收人后粘贴")
        except ValueError as error:
            self.status.setStringValue_(str(error))

    def fillCandidate_(self, sender):
        if self.busy or self.demo:
            return
        try:
            text = self.candidate(sender)
            if self.result_capture is None:
                raise ValueError("手动输入没有可验证的微信会话，请使用复制")
            if self.title_field.stringValue() != self.result_capture.title:
                raise ValueError("会话标题已修改，请重新读取或使用复制")
        except ValueError as error:
            self.status.setStringValue_(str(error))
            return
        original = self.result_capture
        self.busy = True
        self.status.setStringValue_("重新核对微信会话和消息，再填入草稿…")

        def fill():
            from adapter import fill_reply
            return fill_reply(original, text)

        def done(result, error):
            self.busy = False
            self.status.setStringValue_(error or result)
        self.work(fill, done)

    def clear_(self, sender):
        if self.busy:
            self.status.setStringValue_("请等待当前操作完成后清空")
            return
        self.reset_result()
        if self.trend_window:
            self.trend_window.reset()
        self.overlay.reviewing = False
        self.overlay.last_content = None
        self.auto_reading = False
        self.auto_read.setState_(A.NSControlStateValueOff)
        self.captured = None
        self.conversations = Conversations()
        self.auto_gate.configure(False, None)
        self.transcript.setString_("")
        self.title_field.setStringValue_("")
        self.background.setStringValue_("")
        self.confirm.setState_(A.NSControlStateValueOff)
        self.status.setStringValue_("已清空本轮内容")

    def poll_(self, timer):
        while True:
            try:
                callback, value, error = self.events.get_nowait()
            except queue.Empty:
                break
            callback(value, error)
        if self.result_inputs is not None and self.result_inputs != self.inputs():
            self.reset_result()
            self.confirm.setState_(A.NSControlStateValueOff)
            self.status.setStringValue_("输入已变化，请重新核对和分析")
        self.sync_panel()
        if (self.auto_reading and not self.busy and time.monotonic() >= self.next_capture
                and not self.window.isVisible()
                and not (self.settings_screen and self.settings_screen.window.isVisible())
                and not (self.provider_settings and self.provider_settings.window.isVisible())
                and not (self.profile_editor and self.profile_editor.window.isVisible())
                and not getattr(self.overlay, 'reviewing', False)):
            self.read_in_background()


def main():
    app = A.NSApplication.sharedApplication()
    app.setActivationPolicy_(A.NSApplicationActivationPolicyRegular)
    controller = Controller.alloc().init()
    if '--settings' in sys.argv:
        controller.settings_(None)
    elif '--trend' in sys.argv:
        controller.trend_(None)
    elif '--details' in sys.argv:
        controller.details_(None)
    app.run()
    return controller


if __name__ == "__main__":
    main()
