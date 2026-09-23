"""One explicit request: optional Jev strategy, then configured reply generation."""
from client import complete
from core import build_messages, parse_advice, parse_rewrite
from jev import decide
from ranking import rank_candidates
import json

TONE_GUIDANCE = {
    '稳健': '朴素、贴题，像平时接话；不写客服式确认或过度安慰。',
    '会撩': '有双方接梗或亲近的依据才加一点玩笑或欣赏；没有依据就自然接话，不硬撩、不造金句。',
    '直接': '把想说的事说清楚；不命令、不故作冷淡，不把普通聊天写成关系宣言。',
}


def analyze_snapshot(snapshot, scene, background, reply_config, jev_config=None, preferences=None):
    # Prepare/validate local inputs before either external request.
    messages, paths = build_messages(snapshot, scene, background)
    if preferences is not None:
        settings = preferences.as_dict()
        messages[0]['content'] += (
            f"\n回复偏好：{settings['tone']}；每条最多 {settings['max_chars']} 字；最多 {settings['count']} 条候选。"
            + TONE_GUIDANCE[settings['tone']] +
            "会撩需结合互惠反馈，直接指清晰表达和边界。偏好不得覆盖事实、拒绝或停止条件。")
    decision = decide(jev_config, snapshot, scene, background) if jev_config else None
    if decision:
        import json
        messages[0]["content"] += (
            "\n本轮主策略已由独立 Jev 决策步骤选定，strategy 字段必须为：" + decision.strategy +
            "。围绕它生成分析与回复；可以建议不回复并返回空候选。" +
            "这些概率只反映模型对策略选择的不确定性，不是关系事实或回复成功率。")
        payload = json.loads(messages[1]["content"])
        payload["strategy_decision"] = decision.as_dict()
        messages[1]["content"] = json.dumps(payload, ensure_ascii=False)
    advice = parse_advice(complete(reply_config, messages))
    if preferences is not None and (len(advice['candidates']) > settings['count'] or any(
            len(candidate['text']) > settings['max_chars'] for candidate in advice['candidates'])):
        raise ValueError('模型未遵守候选数量或长度设置；未展示候选，请重试')
    if decision:
        if advice["strategy"] != decision.strategy:
            raise ValueError("回复模型未遵循 Jev 选定的策略；未展示候选，请重试")
        advice["jev_decision"] = decision.as_dict()
    return rank_candidates(reply_config, snapshot, scene, background, advice, preferences)


def rewrite_snapshot(snapshot, scene, background, reply_config, previous, preferences=None):
    """Rewrite only the drafts, retaining the accepted analysis and strategy."""
    if not previous['candidates']:
        raise ValueError('本轮建议不回复，无需改写')
    messages, _ = build_messages(snapshot, scene, background)
    messages[0]['content'] += (
        '\n本轮只改写候选，让它更像用户本人。保留给定事实、意图判断和主策略，不添加安排或承诺。'
        '只从当前可靠归属于用户的原话学习口吻；没有样本时用朴素口语。'
        '不靠随机语气词或错字制造差异，已经自然的内容可以保留。'
        '只输出 JSON 对象，包含 candidates 数组；每条含 text、reason、tradeoff。'
        'strategy 若出现必须为：' + previous['strategy'])
    if preferences:
        settings = preferences.as_dict()
        messages[0]['content'] += (f"\n每条最多 {settings['max_chars']} 字，最多 {settings['count']} 条。"
                                   + TONE_GUIDANCE[settings['tone']])
    payload = json.loads(messages[1]['content'])
    payload['accepted_analysis'] = {key: previous[key] for key in (
        'facts', 'hypotheses', 'unknowns', 'strategy', 'recommendation', 'stop_condition', 'candidates')}
    messages[1]['content'] = json.dumps(payload, ensure_ascii=False)
    candidates = parse_rewrite(complete(reply_config, messages), previous['strategy'])
    if not candidates:
        raise ValueError('改写未返回候选，已保留原回复')
    if preferences and (len(candidates) > preferences.count or any(
            len(row['text']) > settings['max_chars'] for row in candidates)):
        raise ValueError('改写未遵守数量或长度，已保留原回复')
    result = dict(previous, candidates=candidates)
    return rank_candidates(reply_config, snapshot, scene, background, result, preferences)
