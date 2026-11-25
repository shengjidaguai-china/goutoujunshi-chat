package com.jev.probe.jev

import org.junit.Assert.assertEquals
import org.junit.Test

class JevQuestionsTest {
    @Test fun ranksTwoRepliesWithoutAddingAnEmptyThirdOption() {
        val candidates = listOf("好呀，周六晚上见！", "有空呀，想吃哪家？")
        val criteria = JevQuestions.rankQuestion(candidates)
            .getJSONObject("best_reply").getJSONObject("criteria")

        assertEquals(2, criteria.length())
        assertEquals(candidates[0], criteria.getString("reply_a"))
        assertEquals(candidates[1], criteria.getString("reply_b"))
    }
}
