"""Dogtoujunshi's evidence-first reading of Jev's structured answers.

This module does not infer new facts from OCR. The short quotes are explicitly
marked as text to check in WeChat, and Jev confidence is never a success rate.
"""
from __future__ import annotations

from math import isfinite

try:
    from .questions import CHOICE_LABELS
except ImportError:
    from questions import CHOICE_LABELS

_NEXT = {
    "check_history": "先核对原聊天，再决定怎么回。",
    "apologize": "只为已经确认的问题道歉，观察对方是否愿意继续谈。",
    "give_commitment": "确认自己真能做到的时间和行动，再给出承诺。",
    "explain": "只说明自己知道的事实，缺的部分先查证。",
    "acknowledge": "接住对方这句话，留出对方继续表达的空间。",
    "say_less": "这轮可以少说，必要时不回复，等明确的新信息。",
    "make_plan": "提出可执行的安排，并让对方选择或修正。",
}


def _message_parts(message):
    if isinstance(message, dict):
        return message.get("from"), str(message.get("text") or "")
    return message[0], str(message[1])


def explicit_boundary(messages: list) -> bool:
    """Only the latest *other* message can trigger a conservative no-draft exit."""
    if not messages:
        return False
    who, text = _message_parts(messages[-1])
    if who != "her":
        return False
    return any(term in text for term in (
        "不要再联系我", "别再联系我", "不要再给我发消息", "别再给我发消息",
        "不要再找我", "别再找我", "请不要联系我"))


def brief(messages: list, answers: dict) -> dict:
    """Compact display contract shared by the Windows overlay and CLI checks."""
    observed = []
    for message in messages[-8:]:
        who, text = _message_parts(message)
        if who in ("me", "her") and text.strip():
            observed.append(("我" if who == "me" else "对方") + "：「" + text.strip()[:100] + "」")
    intent_row = (answers.get("true_intent") or {})
    intent_key = intent_row.get("choice")
    intent = CHOICE_LABELS["true_intent"].get(intent_key, "暂无法判断")
    confidence = intent_row.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not isfinite(confidence) or not 0 <= confidence <= 1:
        confidence = None
    action_key = (answers.get("best_action") or {}).get("choice")
    action = CHOICE_LABELS["best_action"].get(action_key, "先核对原文")
    boundary = explicit_boundary(messages)
    return {
        "facts": observed[-3:],
        "intent": "可能是" + intent if intent_key else "证据不足，暂无法判断",
        "intent_confidence": confidence if observed and not boundary else None,
        "action": "尊重对方停止联系的要求" if boundary else action,
        "unknown": "仅凭屏幕片段无法确认对方内心、完整上下文和线下情况。",
        "next_step": "先停止联系；只有对方主动重启对话再评估。" if boundary else _NEXT.get(action_key, "先核对原文，再决定下一步。"),
        "stop_condition": "对方明确拒绝或要求停止联系时，停止推进。",
        "evidence_note": "以上引文来自 OCR，须核对原文和说话人；把握度是模型估计，不是对方真实意图概率。",
    }
