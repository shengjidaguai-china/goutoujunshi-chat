package com.jev.probe.keyboard

import kotlin.math.abs

internal data class TranscriptLine(val text: String, var side: String, var included: Boolean = true)

internal object KeyboardOcrTranscript {
    data class Box(
        val text: String,
        val left: Int,
        val top: Int,
        val right: Int,
        val bottom: Int,
        val blockIndex: Int? = null,
        val separatedSuffix: String? = null
    ) {
        val centerX get() = (left + right) / 2.0
        val centerY get() = (top + bottom) / 2.0
        val height get() = (bottom - top).coerceAtLeast(1)
    }

    private val rolePrefix = Regex("""^(我|对方)\s*[:：]\s*(?=\S)""")
    private val timeLabel = Regex("""^(?:(?:今天|昨天|上午|下午)\s*)?\d{1,2}[:：]\d{2}(?:\s*(?:[AP]M|[A-Z]))?$""")
    private val composerHint = Regex("""^(?:输入(?:消息|文字|内容)|说点什么|Type a message|Enter message)[…\.。\s]*$""")

    fun parse(boxes: List<Box>, width: Int, height: Int): List<TranscriptLine> {
        val ordered = boxes.filter { it.text.isNotBlank() }.sortedWith(compareBy(Box::top, Box::left))
        val statusTime = ordered.firstOrNull {
            it.centerY < height * 0.045 && timeLabel.matches(it.text.trim())
        }
        val messages = mutableListOf<TranscriptLine>()
        var previous: Box? = null
        for (box in ordered) {
            val raw = textWithoutAvatar(box, width)
            val role = rolePrefix.find(raw)
            val centered = abs(box.centerX - width / 2.0) <= width * 0.14
            val chrome = role == null && when {
                statusTime != null && box.centerY < height * 0.045 &&
                    abs(box.centerY - statusTime.centerY) <= statusTime.height -> true
                // An isolated time inside a bubble can be a legitimate reply.
                timeLabel.matches(raw) && (box.centerY < height * 0.045 || centered) -> true
                statusTime != null && centered && box.centerY < height * 0.105 && raw.length <= 32 -> true
                box.centerY > height * 0.72 && composerHint.matches(raw) -> true
                statusTime != null && centered && box.centerY > height * 0.87 && box.height < height * 0.022 -> true
                raw == "我" && box.left > width * 0.88 -> true
                else -> false
            }
            val prior = previous
            val last = messages.lastOrNull()
            if (!chrome && role == null && prior != null && last?.included == true && wraps(prior, box, width)) {
                val separator = if (last.text.last().isAsciiWordChar() && raw.first().isAsciiWordChar()) " " else ""
                messages[messages.lastIndex] = last.copy(text = last.text + separator + raw)
            } else {
                val side = when {
                    role?.groupValues?.get(1) == "我" -> "me"
                    role != null -> "other"
                    box.centerX > width * 0.56 -> "me"
                    else -> "other"
                }
                messages.add(TranscriptLine(raw.drop(role?.value?.length ?: 0), side, included = !chrome))
            }
            previous = box
        }
        return messages.takeLast(50).map { it.copy(text = it.text.take(400)) }
    }

    private fun textWithoutAvatar(box: Box, width: Int): String {
        val text = box.text.trim()
        if (text.length > 1 && box.right > width * 0.9 && box.separatedSuffix == "我") {
            return text.removeSuffix("我").trimEnd()
        }
        return text
    }

    private fun wraps(previous: Box, next: Box, width: Int): Boolean {
        val lineHeight = minOf(previous.height, next.height)
        val gap = next.top - previous.bottom
        if (gap < -lineHeight * 0.3 || gap > lineHeight * 0.8) return false
        // A wrapped bubble usually shares a left edge even when it is sent from the right.
        if (abs(next.left - previous.left) <= maxOf(lineHeight * 0.5, width * 0.025)) return true
        return previous.blockIndex != null && previous.blockIndex == next.blockIndex &&
            next.left >= previous.left && next.right <= previous.right
    }

    private fun Char.isAsciiWordChar() = this in 'a'..'z' || this in 'A'..'Z' || this in '0'..'9'
}
