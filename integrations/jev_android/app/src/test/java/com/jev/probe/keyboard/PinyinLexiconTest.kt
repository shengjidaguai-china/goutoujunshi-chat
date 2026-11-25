package com.jev.probe.keyboard

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class PinyinLexiconTest {
    @Test fun bundledDictionaryFindsEverydayPhrasesOnBothLayouts() {
        val lexicon = File("src/main/assets/pinyin/pinyin.tsv").reader().use { PinyinLexicon(it) }

        assertEquals("你好", lexicon.candidates("nihao", false).first())
        assertTrue("你好" in lexicon.candidates("64426", true))
        assertEquals("谢谢", lexicon.candidates("xiexie", false).first())
    }

    @Test fun unseenPhraseCanBeTypedWithoutChangingInputMode() {
        val lexicon = PinyinLexicon("ni\t你\t100\nhao\t好\t100\n".reader())

        assertEquals(listOf("你好"), lexicon.candidates("nihao", false))
        assertEquals(listOf("你好"), lexicon.candidates("64426", true))
        assertEquals(listOf("好"), lexicon.candidates("ha", false))
        assertTrue(lexicon.candidates("h".repeat(33), false).isEmpty())
    }
}
