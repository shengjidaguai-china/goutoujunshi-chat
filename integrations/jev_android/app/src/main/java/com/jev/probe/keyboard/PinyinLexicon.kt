package com.jev.probe.keyboard

import java.io.Reader
import kotlin.math.ln

/** Small offline lexicon for both QWERTY spelling and T9 digit sequences. */
internal class PinyinLexicon(reader: Reader) {
    private data class Word(val text: String, val weight: Int)
    private data class Segment(val text: String, val score: Double)

    private val full = HashMap<String, List<Word>>()
    private val nine = HashMap<String, List<Word>>()
    private val fullCodes: List<String>
    private val nineCodes: List<String>

    init {
        val entries = HashMap<String, MutableList<Word>>()
        reader.buffered().useLines { lines ->
            lines.filterNot { it.startsWith('#') }.forEach { line ->
                val fields = line.split('\t', limit = 4)
                if (fields.size >= 3 && fields[0].isNotEmpty() && fields[1].isNotEmpty()) {
                    val weight = fields[2].toIntOrNull() ?: 1
                    entries.getOrPut(fields[0]) { ArrayList() }.add(Word(fields[1], weight))
                }
            }
        }
        val digitEntries = HashMap<String, MutableList<Word>>()
        entries.forEach { (code, words) ->
            val best = ranked(words)
            full[code] = best
            digitEntries.getOrPut(toDigits(code)) { ArrayList() }.addAll(best)
        }
        digitEntries.forEach { (code, words) -> nine[code] = ranked(words) }
        fullCodes = full.keys.sorted()
        nineCodes = nine.keys.sorted()
    }

    fun candidates(raw: String, nineKey: Boolean): List<String> {
        if (raw.isEmpty() || raw.length > MAX_INPUT) return emptyList()
        val words = if (nineKey) nine else full
        val codes = if (nineKey) nineCodes else fullCodes
        val result = LinkedHashSet<String>()
        words[raw]?.forEach { result += it.text }
        // Join the most likely words when the full phrase isn't in the lexicon.
        val segments = arrayOfNulls<Segment>(raw.length + 1)
        segments[0] = Segment("", 0.0)
        for (start in raw.indices) {
            val prior = segments[start] ?: continue
            for (end in start + 1..raw.length) {
                val word = words[raw.substring(start, end)]?.firstOrNull() ?: continue
                val score = prior.score + ln(word.weight.coerceAtLeast(1).toDouble()) - 16.0
                if (score > (segments[end]?.score ?: Double.NEGATIVE_INFINITY))
                    segments[end] = Segment(prior.text + word.text, score)
            }
        }
        segments.last()?.let { result += it.text }
        val first = codes.binarySearch(raw).let { if (it < 0) -it - 1 else it }
        val completions = ArrayList<Word>()
        for (index in first until minOf(first + 48, codes.size)) {
            val code = codes[index]
            if (!code.startsWith(raw)) break
            if (code != raw) completions.addAll(words[code].orEmpty().take(3))
        }
        ranked(completions).forEach { result += it.text }
        return result.take(CANDIDATE_LIMIT)
    }

    private fun ranked(words: List<Word>): List<Word> =
        words.sortedByDescending { it.weight }.distinctBy { it.text }.take(CANDIDATE_LIMIT)

    companion object {
        const val MAX_INPUT = 32
        private const val CANDIDATE_LIMIT = 10
        private const val DIGITS = "22233344455566677778889999"

        private fun toDigits(code: String): String = code.map { ch -> DIGITS.getOrElse(ch - 'a') { ch } }.joinToString("")
    }
}
