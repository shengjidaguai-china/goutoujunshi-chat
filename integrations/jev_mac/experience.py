"""Portable settings, per-conversation context and automatic-analysis gate."""
import json
import time
import uuid
from dataclasses import dataclass

STAGES = ('未填写', '初识', '了解中', '暧昧', '约会中', '伴侣', '关系结束')
GOALS = {'自然接话': '日常回复', '主动邀约': '邀约推进', '澄清关系': '日常回复',
         '修复冲突': '冲突修复', '减少投入': '投入与退出', '结束联系': '投入与退出'}
TONES = ('稳健', '会撩', '直接')
LENGTHS = {'简短': 40, '适中': 70, '详细': 100}
PROFILE_FIELDS = ('stage', 'goal', 'background', 'my_mbti', 'their_mbti', 'my_score', 'their_score', 'notes')


@dataclass(frozen=True)
class ReplyPreferences:
    tone: str = '稳健'
    length: str = '简短'
    count: int = 3

    def __post_init__(self):
        if self.tone not in TONES or self.length not in LENGTHS or type(self.count) is not int or not 1 <= self.count <= 3:
            raise ValueError('请选择有效的回复口吻、长度和候选数量')

    def as_dict(self):
        return {'tone': self.tone, 'length': self.length, 'count': self.count, 'max_chars': LENGTHS[self.length]}


def empty_profile(label='当前会话'):
    return dict(id='mac-' + uuid.uuid4().hex, label=label, stage='未填写', goal='自然接话',
                background='', my_mbti='', their_mbti='', my_score='', their_score='', notes='')


def validate_profile(profile):
    if profile.get('stage') not in STAGES or profile.get('goal') not in GOALS:
        raise ValueError('请选择关系阶段和本轮目标')
    for key in ('label',) + PROFILE_FIELDS:
        if not isinstance(profile.get(key), str) or len(profile[key]) > 200:
            raise ValueError('每项资料最多 200 字；不确定的信息可以留空')
    for key in ('my_score', 'their_score'):
        score = profile[key].strip()
        if score and (not score.isdigit() or not 0 <= int(score) <= 100):
            raise ValueError('主观综合评分请填 0–100；不知道可留空')
    if not profile['label'].strip():
        raise ValueError('请给当前对象填写一个称呼或代号')
    return dict(profile)


def profile_context(profile):
    # Never serialize the profile identifier or window bindings into model input.
    return json.dumps({k: profile[k] for k in ('label',) + PROFILE_FIELDS if profile.get(k)}, ensure_ascii=False)


class Conversations:
    def __init__(self):
        self.profiles = {}
        self.bindings = {}
        self.current_key = None
        self.current = empty_profile()
        self.profiles[self.current['id']] = self.current

    @staticmethod
    def key(snapshot):
        valid_title = snapshot.title and not (snapshot.source == 'deepseek_ocr' and snapshot.title in ('微信', 'WeChat'))
        return (snapshot.window_id, snapshot.title) if snapshot.source in ('ocr', 'deepseek_ocr') and snapshot.window_id and valid_title else None

    def select(self, snapshot):
        key = self.key(snapshot)
        if key != self.current_key:
            self.current_key = key
            identity = self.bindings.get(key) if key else None
            if identity is None:
                self.current = empty_profile(snapshot.title or '当前会话')
                self.profiles[self.current['id']] = self.current
                if key:
                    self.bindings[key] = self.current['id']
            else:
                self.current = self.profiles[identity]
        return self.current

    def bind(self, identity):
        if identity not in self.profiles:
            raise ValueError('请选择已存在的对象')
        self.current = self.profiles[identity]
        if self.current_key:
            self.bindings[self.current_key] = identity

    def update(self, profile):
        self.current = validate_profile(profile)
        self.profiles[self.current['id']] = self.current


class AutoGate:
    """Opt-in to a specific observed window/title; stable text, once per change."""
    def __init__(self):
        self.allowed = set()
        self.enabled = False
        self.pending = None
        self.observed_at = 0
        self.attempted = set()
        self.last_attempt = float('-inf')

    def configure(self, enabled, key, baseline=None):
        if enabled and key is None:
            raise ValueError('请先读取并核对要自动分析的会话')
        self.enabled = bool(enabled)
        self.allowed = {key} if enabled else set()
        self.pending = None
        self.attempted.clear()
        if baseline:
            self.attempted.add(baseline)

    def ready(self, snapshot, now=None):
        now = time.monotonic() if now is None else now
        if not self.enabled or Conversations.key(snapshot) not in self.allowed:
            self.pending = None
            return False
        lines = [line for line in snapshot.transcript.splitlines() if line.strip()]
        if not lines or not lines[-1].startswith('对方') or any(
                marker in snapshot.transcript for marker in ('说话人待确认', 'OCR待核对')):
            self.pending = None
            return False
        if snapshot.identity != self.pending:
            self.pending, self.observed_at = snapshot.identity, now
            return False
        if now - self.observed_at < 2 or now - self.last_attempt < 10 or snapshot.identity in self.attempted:
            return False
        self.attempted.add(snapshot.identity)
        # Bounded history; no retries of the newest attempt, no transcripts retained.
        if len(self.attempted) > 256:
            self.attempted = {snapshot.identity}
        self.last_attempt = now
        return True
