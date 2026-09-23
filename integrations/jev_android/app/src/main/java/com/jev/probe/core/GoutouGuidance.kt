package com.jev.probe.core

/** Evidence-first rules shared by the Android draft prompt and overlay. */
object GoutouGuidance {
    private val noContact = listOf(
        "不要再联系我", "别再联系我", "不要再给我发消息", "别再给我发消息",
        "不要再找我", "别再找我", "请不要联系我"
    )

    fun explicitBoundary(snapshot: ChatSnapshot): Boolean {
        val latest = snapshot.messages.lastOrNull() ?: return false
        return latest.side == "other" && noContact.any { latest.text.contains(it) }
    }

    fun nextStep(action: String?): String = when (action) {
        "check_history" -> "先核对原聊天，再决定怎么回。"
        "apologize" -> "只为已确认的问题道歉，观察对方是否愿意继续谈。"
        "give_commitment" -> "确认自己真能做到的时间和行动，再给出承诺。"
        "explain" -> "只说明自己知道的事实，缺的部分先查证。"
        "acknowledge" -> "接住这句话，留出对方继续表达的空间。"
        "say_less" -> "这轮可以少说，必要时不回复。"
        "make_plan" -> "提出可执行的安排，并让对方选择或修正。"
        else -> "先核对原文，再决定下一步。"
    }

    const val stopCondition = "对方明确拒绝或要求停止联系时，停止推进。"

    const val draftRules = """
狗头军师规则：先区分可见事实、暂定推测与仍未知；一轮回复只做一个主动作。
对方的意图只是可能解释，别在回复里宣称看穿了 TA。
尊重拒绝与边界；不以得到某个人为唯一目标，不使用操控、施压、贬低或虚假时间限制。
不要编造见面时间、共同经历、自己做过的事或做不到的承诺。
回复像用户平时发的一句话；不把分析术语、理由、代价塞进可发送文本。
"""
}
