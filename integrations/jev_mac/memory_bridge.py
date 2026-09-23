"""UI adapter for the existing consent-gated memory CLI. Payloads use stdin."""
import json
import subprocess
import sys
from pathlib import Path
from experience import PROFILE_FIELDS, empty_profile, validate_profile

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts' / 'memory_store.py'


class MemoryBridge:
    def __init__(self, env=None):
        self.env = env
        self.last_operations = []

    def call(self, command, *args, payload=None):
        try:
            result = subprocess.run([sys.executable, '-B', str(SCRIPT), command, *args],
                                    input=json.dumps(payload, ensure_ascii=False) if payload else None,
                                    capture_output=True, text=True, timeout=10, env=self.env)
            data = json.loads(result.stdout)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            raise ValueError('档案操作失败，请检查本地存储权限') from None
        if result.returncode:
            raise ValueError('档案操作未完成：请检查是否已启用、暂停或达到容量上限')
        return data

    def active(self):
        state = self.call('status')
        return state.get('consent_enabled') and not state.get('paused')

    def list_profiles(self):
        if not self.active():
            return []
        rows = self.call('show')['memories']
        return [(row['subject_id'], row['value']) for row in rows
                if row['subject_id'].startswith('mac-') and row['field'] == 'display_label']

    def load_profile(self, identity):
        if not self.active():
            raise ValueError('档案未启用或已暂停')
        rows = self.call('show', '--subject-id', identity)['memories']
        profile = empty_profile()
        profile['id'] = identity
        for row in rows:
            if row['subject_id'] != identity:
                continue
            if row['field'] == 'display_label':
                profile['label'] = row['value']
            elif row['field'] in PROFILE_FIELDS:
                profile[row['field']] = '' if row['value'] == '未填写' and row['field'] not in ('stage', 'goal') else row['value']
        return validate_profile(profile)

    def save_profile(self, profile):
        validate_profile(profile)
        if not self.active():
            return 0
        previous = {row['field']: row['value'] for row in self.call('show', '--subject-id', profile['id'])['memories']
                    if row['subject_id'] == profile['id']}
        operations = []
        for key in ('label',) + PROFILE_FIELDS:
            field = 'display_label' if key == 'label' else key
            old = previous.get(field, '')
            if old == '未填写' and key not in ('stage', 'goal'):
                old = ''
            if old == profile[key]:
                continue
            # Empty strings explicitly clear old optional values; the CLI accepts
            # nonempty values only, so represent unknown with a neutral marker.
            value = profile[key] or '未填写'
            result = self.call('apply', payload={'scope': 'object' if key == 'label' else 'relationship',
                'subject_id': profile['id'], 'field': field, 'value': value,
                'source_type': 'user_explicit', 'source_ref': 'Mac 设置页', 'confidence': 'high'})
            if result.get('op_id'):
                operations.append(result['op_id'])
                self.last_operations = list(operations)
        return len(operations)

    def undo_save(self):
        if not self.last_operations:
            raise ValueError('本次运行没有可撤销的档案保存')
        while self.last_operations:
            self.call('undo', '--op-id', self.last_operations[-1])
            self.last_operations.pop()
