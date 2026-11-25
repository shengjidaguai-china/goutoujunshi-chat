package com.jev.probe.keyboard

import com.jev.probe.keyboard.KeyboardOcrTranscript.Box
import org.junit.Assert.assertEquals
import org.junit.Test

class KeyboardOcrTranscriptTest {
    @Test fun wholeScreenKeepsUiTextOutOfAnalysisButAllowsRestoringIt() {
        val lines = KeyboardOcrTranscript.parse(listOf(
            Box("10:23 D", 68, 5, 143, 26),
            Box("03G1白", 567, 8, 665, 29),
            Box("我是好人", 320, 80, 457, 113),
            Box("对方：10:30", 125, 165, 227, 194),
            Box("我:周六下午有空", 135, 228, 345, 254),
            Box("输入消息...", 52, 1077, 168, 1100),
            Box("忙碌推迟，时间还没定 · 22 条消息", 103, 1163, 615, 1182)
        ), 720, 1280)

        assertEquals(listOf("10:30", "周六下午有空"), lines.filter { it.included }.map { it.text })
        assertEquals(listOf("other", "me"), lines.filter { it.included }.map { it.side })
        assertEquals(listOf("10:23 D", "03G1白", "我是好人", "输入消息...", "忙碌推迟，时间还没定 · 22 条消息"),
            lines.filterNot { it.included }.map { it.text })
    }

    @Test fun wrappedMessagesKeepTheirSpeakerAndSeparateFromTheNextBubble() {
        val lines = KeyboardOcrTranscript.parse(listOf(
            Box("我:周末出去换换空气吧，那个展还开 我", 117, 337, 670, 367, 6, "我"),
            Box("着", 118, 375, 142, 400, 7),
            Box("对方：这周末可能也要收尾，我现在还", 126, 453, 600, 481, 8),
            Box("说不准", 126, 494, 212, 521, 8),
            Box("我：我周六下午比较空", 134, 542, 387, 569, 8),
            Box("我：想顺路去看看", 147, 576, 360, 603, 8)
        ), 720, 1280)

        assertEquals(listOf(
            TranscriptLine("周末出去换换空气吧，那个展还开着", "me"),
            TranscriptLine("这周末可能也要收尾，我现在还说不准", "other"),
            TranscriptLine("我周六下午比较空", "me"),
            TranscriptLine("想顺路去看看", "me")
        ), lines)
    }

    @Test fun aMessageThatEndsWithMeKeepsItsLastCharacter() {
        val lines = KeyboardOcrTranscript.parse(listOf(
            Box("我：有什么可以问我", 390, 230, 666, 257)
        ), 720, 1280)

        assertEquals(listOf(TranscriptLine("有什么可以问我", "me")), lines)
    }

    @Test fun croppedChatDoesNotTreatItsFirstMessageAsAConversationTitle() {
        val lines = KeyboardOcrTranscript.parse(listOf(
            Box("Hi there!", 285, 20, 425, 47),
            Box("10:30", 66, 104, 150, 130)
        ), 720, 1280)

        assertEquals(listOf("Hi there!", "10:30"), lines.filter { it.included }.map { it.text })
    }
}
