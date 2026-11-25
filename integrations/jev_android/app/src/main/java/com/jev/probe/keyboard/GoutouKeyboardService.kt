package com.jev.probe.keyboard

import android.content.Intent
import android.graphics.Bitmap
import android.inputmethodservice.InputMethodService
import android.net.Uri
import android.os.Handler
import android.os.Looper
import android.text.InputType
import android.text.SpannableString
import android.text.TextUtils
import android.text.style.RelativeSizeSpan
import android.view.Gravity
import android.view.View
import android.view.WindowInsets
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import com.jev.probe.CaptureInputActivity
import com.jev.probe.capture.ocr.CaptureHandoff
import com.jev.probe.capture.ocr.CaptureReadiness
import com.jev.probe.capture.ocr.MlKitOcr
import com.jev.probe.capture.ocr.ScreenCapture
import com.jev.probe.core.Analysis
import com.jev.probe.core.ChatSnapshot
import com.jev.probe.core.GoutouGuidance
import com.jev.probe.core.Msg
import com.jev.probe.core.Prefs
import com.jev.probe.core.WorkScope
import com.jev.probe.core.WorkToken
import com.jev.probe.jev.JevClient
import com.jev.probe.jev.VisionClient
import com.jev.probe.keyboard.KeyboardUi.Icon
import com.jev.probe.keyboard.KeyboardUi.Key
import java.util.concurrent.Executors

/** Standard Android IME. Image requests and advice are scoped to the initiating editor. */
class GoutouKeyboardService : InputMethodService() {
    private enum class Page { TYPE, MENU, WAIT_IMAGE, PREVIEW, OCR, REVIEW, ANALYZE, REPLIES }

    private data class Editor(val pkg: String, val field: Int, val name: String?, val type: Int) {
        val kind get() = type and InputType.TYPE_MASK_CLASS
        val secure get() = when (kind) {
            InputType.TYPE_CLASS_TEXT -> (type and InputType.TYPE_MASK_VARIATION) in setOf(
                InputType.TYPE_TEXT_VARIATION_PASSWORD, InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD,
                InputType.TYPE_TEXT_VARIATION_WEB_PASSWORD
            )
            InputType.TYPE_CLASS_NUMBER ->
                type and InputType.TYPE_MASK_VARIATION == InputType.TYPE_NUMBER_VARIATION_PASSWORD
            else -> false
        }
        val chatAllowed get() = kind == InputType.TYPE_CLASS_TEXT && !secure
    }

    private class ImageRound(val editor: Editor) { var requestId: String? = null }

    private val main = Handler(Looper.getMainLooper())
    private val worker = Executors.newSingleThreadExecutor()
    private val prefs by lazy { Prefs(this) }
    private val keyboardPrefs by lazy { getSharedPreferences("goutou_keyboard_ui", MODE_PRIVATE) }
    private val ocr = MlKitOcr()
    private val chrome by lazy { KeyboardUi(this) }
    private val assistant by lazy { KeyboardAssistantPanel(this, chrome) }
    private var root: LinearLayout? = null
    private var candidateRow: LinearLayout? = null
    private var editor: Editor? = null
    private var viewActive = false
    private var destroyed = false
    private var page = Page.TYPE
    private var imageRound: ImageRound? = null
    private var expiry: Runnable? = null
    private var preview: Bitmap? = null
    private var work: WorkToken? = null
    private var transcript = emptyList<TranscriptLine>()
    private var analysis: Analysis? = null
    private var status: String? = null
    private var lexicon: PinyinLexicon? = null
    private var lexiconFailed = false
    private var spelling = ""
    private var words = emptyList<String>()
    private var nine = false
    private var chinese = true
    private var numbers = false
    private var shifted = false

    override fun onCreate() {
        super.onCreate()
        nine = keyboardPrefs.getBoolean("nine", false)
        chinese = keyboardPrefs.getBoolean("chinese", true)
        worker.execute {
            val dictionary = runCatching {
                assets.open("pinyin/pinyin.tsv").reader(Charsets.UTF_8).use { PinyinLexicon(it) }
            }.getOrNull()
            main.post {
                if (destroyed) return@post
                lexicon = dictionary
                lexiconFailed = dictionary == null
                updateCandidates()
            }
        }
    }

    override fun onEvaluateFullscreenMode() = false

    override fun onCreateInputView(): View = chrome.column().apply {
        root = this
        chrome.padded(this, 5, 4)
        setOnApplyWindowInsetsListener { view, insets ->
            val bars = insets.getInsets(WindowInsets.Type.navigationBars())
            view.setPadding(chrome.dp(5) + bars.left, chrome.dp(4), chrome.dp(5) + bars.right,
                chrome.dp(4) + bars.bottom)
            insets
        }
        render()
    }

    override fun onStartInput(attribute: EditorInfo?, restarting: Boolean) {
        super.onStartInput(attribute, restarting)
        val next = attribute.toEditor()
        if (imageRound == null && (!restarting || editor != next)) {
            reset(Page.TYPE)
            numbers = next?.kind == InputType.TYPE_CLASS_NUMBER || next?.kind == InputType.TYPE_CLASS_PHONE
            shifted = false
        }
        editor = next
    }

    override fun onStartInputView(info: EditorInfo?, restarting: Boolean) {
        super.onStartInputView(info, restarting)
        viewActive = true
        editor = info.toEditor()
        val pending = imageRound
        if (pending != null) {
            if (pending.editor != editor) reset(Page.TYPE)
            else if (pending.requestId == null) clearImageRound()
        }
        render()
    }

    override fun onFinishInputView(finishingInput: Boolean) {
        viewActive = false
        if (imageRound == null) reset(Page.TYPE)
        super.onFinishInputView(finishingInput)
    }

    override fun onFinishInput() {
        viewActive = false
        editor = null
        if (imageRound == null) reset(Page.TYPE)
        super.onFinishInput()
    }

    override fun onDestroy() {
        destroyed = true
        reset(Page.TYPE)
        worker.shutdown()
        root = null
        candidateRow = null
        super.onDestroy()
    }

    private fun EditorInfo?.toEditor(): Editor? = this?.packageName?.let {
        Editor(it, fieldId, fieldName, inputType)
    }

    private fun currentEditor(): Editor? =
        if (currentInputStarted && currentInputConnection != null) currentInputEditorInfo.toEditor() else null

    private fun reset(to: Page) {
        val oldImage = preview
        preview = null
        clearImageRound()
        work?.cancel()
        work = null
        transcript = emptyList()
        analysis = null
        status = null
        spelling = ""
        words = emptyList()
        page = to
        render()
        oldImage?.recycle()
    }

    private fun clearImageRound() {
        val id = imageRound?.requestId
        imageRound = null // Cancel callbacks may run immediately.
        expiry?.let { main.removeCallbacks(it) }
        expiry = null
        if (id != null) CaptureHandoff.cancel(id)
    }

    private fun launchImage(pick: Boolean) {
        val target = editor?.takeIf { it.chatAllowed && it == currentEditor() && viewActive } ?: return
        reset(Page.WAIT_IMAGE)
        val round = ImageRound(target)
        imageRound = round
        round.requestId = CaptureHandoff.register(CaptureHandoff.Request(
            isActive = { imageRound === round },
            readiness = {
                val actual = currentEditor()
                when {
                    actual == target -> CaptureReadiness.READY
                    viewActive && actual != null -> CaptureReadiness.CHANGED
                    else -> CaptureReadiness.WAIT
                }
            },
            setHidden = { hide -> if (hide && viewActive) requestHideSelf(0) },
            onResult = { result -> acceptImage(round, result) }
        ))
        expiry = Runnable {
            if (imageRound === round) {
                reset(if (viewActive && currentEditor() == target) Page.MENU else Page.TYPE)
                if (viewActive) {
                    status = "取图已超时，请重试"
                    render()
                }
            }
        }.also { main.postDelayed(it, 120_000) }
        try {
            startActivity(Intent(this, CaptureInputActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                .putExtra(CaptureInputActivity.EXTRA_REQUEST, round.requestId)
                .putExtra(CaptureInputActivity.EXTRA_PICK_IMAGE, pick))
        } catch (_: Exception) {
            reset(Page.MENU)
            status = "无法打开系统取图入口"
            render()
        }
    }

    private fun acceptImage(round: ImageRound, result: ScreenCapture.Result) {
        if (imageRound !== round || (viewActive && currentEditor() != round.editor)) {
            if (result is ScreenCapture.Result.Ok) result.bitmap.recycle()
            if (imageRound === round) reset(Page.TYPE)
            return
        }
        round.requestId = null
        when (result) {
            is ScreenCapture.Result.Ok -> { preview = result.bitmap; page = Page.PREVIEW }
            is ScreenCapture.Result.Failed -> { status = result.humanMessage; page = Page.MENU }
        }
        if (viewActive) {
            clearImageRound()
            render()
        } else if (currentEditor() == round.editor) {
            requestShowSelf(InputMethodManager.SHOW_IMPLICIT)
        }
    }

    private fun recognize(cloud: Boolean) {
        if (!viewActive || editor != currentEditor()) return
        val bitmap = preview ?: return
        if (cloud && (prefs.effectiveVisionKey().isBlank() || !VisionClient.supportsVision(prefs.visionBaseUrl))) {
            status = "请先在 App 设置里配置视觉接口，或切换到本地识图"
            render()
            return
        }
        val width = bitmap.width
        val height = bitmap.height
        preview = null
        status = null
        page = Page.OCR
        val token = WorkToken().also { work = it }
        render() // Detach the preview view before the worker owns the bitmap.
        if (cloud) {
            worker.execute {
                val result = try {
                    WorkScope.run(token) {
                        parseCloudLines(VisionClient(prefs).extractDialog(VisionClient.encodeJpeg(bitmap)))
                    }
                } catch (_: Exception) {
                    emptyList()
                } finally {
                    bitmap.recycle()
                }
                main.post { showTranscript(token, result, "视觉识别失败或没有识别到文字，请检查视觉接口或换图重试") }
            }
        } else {
            val failed = "没有识别到文字，请换一张清晰的聊天截图"
            try {
                ocr.recognize(bitmap, null) { lines ->
                    bitmap.recycle()
                    val boxes = lines.map {
                        val rect = it.bounds
                        KeyboardOcrTranscript.Box(
                            it.text, rect.left, rect.top, rect.right, rect.bottom, it.blockIndex, it.separatedSuffix
                        )
                    }
                    showTranscript(token, KeyboardOcrTranscript.parse(boxes, width, height), failed)
                }
            } catch (_: Exception) {
                bitmap.recycle()
                showTranscript(token, emptyList(), failed)
            }
        }
    }

    private fun parseCloudLines(text: String): List<TranscriptLine> = text.lineSequence().mapNotNull { raw ->
        val line = raw.trim()
        val role = line.substringBefore('：').substringBefore(':')
        val speaker = when (role) { "我" -> "me"; "对方" -> "other"; else -> return@mapNotNull null }
        val body = line.drop(role.length + 1).trim().take(400)
        if (body.isEmpty()) null else TranscriptLine(body, speaker)
    }.toList().takeLast(50)

    private fun showTranscript(token: WorkToken, lines: List<TranscriptLine>, failure: String) {
        if (work !== token || !viewActive || !token.isActive()) return
        work = null
        transcript = lines
        status = if (lines.isEmpty()) failure else null
        page = if (lines.isEmpty()) Page.MENU else Page.REVIEW
        render()
    }

    private fun analyze() {
        val target = editor?.takeIf { it == currentEditor() && it.chatAllowed && viewActive } ?: return
        val msgs = transcript.filter { it.included }.map { Msg(it.side, it.text) }
        if (msgs.isEmpty()) { status = "请至少保留一条对话"; render(); return }
        val snapshot = ChatSnapshot(null, msgs)
        val boundary = GoutouGuidance.explicitBoundary(snapshot)
        if (!boundary && (!prefs.hasKey() || prefs.effectiveReplyKey().isBlank())) {
            status = "请先在 App 设置里配置策略判断和回复接口"
            render()
            return
        }
        status = null
        page = Page.ANALYZE
        val token = WorkToken().also { work = it }
        val relationship = prefs.relationship
        render()
        worker.execute {
            val result = runCatching {
                WorkScope.run(token) {
                    if (boundary) GoutouGuidance.boundaryAnalysis()
                    else {
                        val client = JevClient(prefs)
                        val judgment = client.judge(snapshot, relationship)
                        token.checkActive()
                        if (judgment.error != null) judgment
                        else judgment.copy(rankedReplies = client.draftAndRank(snapshot, relationship, judgment = judgment))
                    }
                }
            }
            main.post {
                if (work !== token || !viewActive || !token.isActive() || currentEditor() != target) return@post
                work = null
                val value = result.getOrNull()
                if (value == null || value.error != null) {
                    status = "分析未完成，请检查配置、余额或网络后重试"
                    page = Page.REVIEW
                } else {
                    analysis = value
                    page = Page.REPLIES
                }
                render()
            }
        }
    }

    private fun render() {
        val ui = root ?: return
        ui.removeAllViews()
        candidateRow = null
        ui.setBackgroundColor(if (page == Page.TYPE) chrome.base else chrome.panel)
        if (page == Page.TYPE) {
            typing(ui)
            return
        }

        val title = when (page) {
            Page.PREVIEW -> "确认图片"
            Page.REVIEW -> "核对对话"
            Page.REPLIES -> "候选回复排序"
            else -> "狗头军师"
        }
        val back: (() -> Unit)? = if (page == Page.MENU) null else ({ reset(Page.MENU) })
        assistant.header(ui, title, back) { reset(Page.TYPE) }
        status?.let { assistant.notice(ui, it) }
        when (page) {
            Page.TYPE -> Unit
            Page.MENU -> assistant.menu(ui, { launchImage(false) }, { launchImage(true) })
            Page.WAIT_IMAGE -> assistant.notice(ui, "完成系统操作后，回到原聊天输入框")
            Page.PREVIEW -> preview?.let { bitmap ->
                val cloud = prefs.ocrEngine == Prefs.OCR_VISION
                val host = if (cloud) Uri.parse(prefs.visionBaseUrl).host.orEmpty() else null
                assistant.preview(ui, bitmap, host) { recognize(cloud) }
            }
            Page.OCR -> assistant.notice(ui, "正在识别图片…", busy = true)
            Page.REVIEW -> assistant.review(ui, transcript, ::analyze)
            Page.ANALYZE -> assistant.notice(ui, "正在分析对话…", busy = true)
            Page.REPLIES -> analysis?.let { result ->
                val origin = editor ?: return@let
                assistant.results(ui, result) { reply ->
                    if (viewActive && isInputViewShown && origin == currentEditor() &&
                        currentInputConnection?.commitText(reply.text, 1) == true
                    ) {
                        reset(Page.TYPE)
                    } else {
                        status = "无法填入，请重新点当前输入框"
                        render()
                    }
                }
            }
        }
    }

    private fun typing(ui: LinearLayout) {
        val secure = editor?.secure == true
        val usePinyin = chinese && !numbers && !secure
        val useNine = usePinyin && nine
        typingToolbar(ui, usePinyin)

        val rows = when {
            numbers -> listOf("1234567890", "@#￥%&*()-+", ".,?!/:;_")
            useNine -> listOf("234", "567", "89")
            else -> listOf("qwertyuiop", "asdfghjkl", "zxcvbnm")
        }
        val keyHeight = if (useNine) 50 else 43
        rows.forEachIndexed { index, chars ->
            val keys = chrome.row()
            if (useNine) {
                val symbol = NINE_PUNCTUATION[index]
                keys.addView(chrome.key(symbol, weight = 0.56f, height = keyHeight, style = Key.UTILITY) {
                    typePunctuation(symbol)
                })
            } else if (!numbers) {
                when (index) {
                    1 -> addInset(keys)
                    2 -> if (usePinyin) {
                        keys.addView(chrome.key("，", weight = 1.5f, height = keyHeight, style = Key.UTILITY) {
                            typePunctuation("，")
                        })
                    } else {
                        keys.addView(chrome.key("⇧", weight = 1.5f, height = keyHeight,
                            style = if (shifted) Key.TINT else Key.UTILITY, description = "切换大小写") {
                            shifted = !shifted
                            render()
                        })
                    }
                }
            }

            for (ch in chars) {
                val direct = if (shifted && !numbers && !usePinyin) ch.uppercaseChar() else ch
                val title = if (useNine) nineTitle(ch) else direct.toString()
                keys.addView(chrome.key(title, height = keyHeight, size = if (useNine) 18f else 19f,
                    description = if (useNine) "$ch ${NINE_LABELS[ch - '2']}" else null) {
                    if (usePinyin) {
                        if (spelling.length < PinyinLexicon.MAX_INPUT) spelling += ch
                        updateCandidates()
                    } else if (commit(direct.toString()) && shifted) {
                        shifted = false
                        render()
                    }
                }.apply { if (useNine) setSingleLine(false) })
            }
            if (index == 1 && !numbers && !useNine) addInset(keys)
            if (index == 2) {
                keys.addView(chrome.key("", weight = if (useNine || numbers) 1f else 1.5f,
                    height = keyHeight, style = Key.UTILITY, icon = Icon.BACKSPACE, description = "退格", onClick = ::erase))
            }
            ui.addView(keys)
        }
        bottomKeys(ui, secure, useNine)
    }

    private fun addInset(row: LinearLayout) {
        row.addView(View(this), LinearLayout.LayoutParams(0, 1, 0.5f))
    }

    private fun nineTitle(digit: Char): CharSequence = SpannableString("$digit\n${NINE_LABELS[digit - '2']}").apply {
        setSpan(RelativeSizeSpan(0.64f), 2, length, 0)
    }

    private fun typingToolbar(ui: LinearLayout, usePinyin: Boolean) {
        ui.addView(chrome.row().apply {
            gravity = Gravity.CENTER_VERTICAL
            chrome.padded(this, 2, 2)
            background = chrome.shape(chrome.panel, 12)
            if (usePinyin) {
                addView(chrome.key(if (nine) "全键" else "九键", weight = 0f, height = 38, style = Key.QUIET,
                    size = 12f, description = if (nine) "切换全键拼音" else "切换九键拼音") {
                    if (finishComposition()) {
                        nine = !nine
                        keyboardPrefs.edit().putBoolean("nine", nine).apply()
                        render()
                    }
                })
                addView(HorizontalScrollView(this@GoutouKeyboardService).apply {
                    isHorizontalScrollBarEnabled = false
                    addView(chrome.row().apply {
                        gravity = Gravity.CENTER_VERTICAL
                        candidateRow = this
                    }, LinearLayout.LayoutParams(-2, -1))
                }, LinearLayout.LayoutParams(0, chrome.dp(42), 1f))
                updateCandidates()
            } else {
                addView(chrome.text(if (numbers) "数字与符号" else "英文键盘", 12f, chrome.secondary).apply {
                    setPadding(chrome.dp(9), 0, 0, 0)
                }, LinearLayout.LayoutParams(0, -2, 1f))
            }
            if (editor?.chatAllowed == true) {
                addView(chrome.key("军师", weight = 0f, height = 38, style = Key.TINT, size = 13f) {
                    reset(Page.MENU)
                }.apply {
                    minimumWidth = chrome.dp(72)
                    setCompoundDrawablesRelative(chrome.mascot(20), null, null, null)
                    compoundDrawablePadding = chrome.dp(3)
                    setPadding(chrome.dp(8), 0, chrome.dp(8), 0)
                })
            }
        }, LinearLayout.LayoutParams(-1, -2).apply {
            setMargins(chrome.dp(2), 0, chrome.dp(2), chrome.dp(5))
        })
    }

    private fun bottomKeys(ui: LinearLayout, secure: Boolean, useNine: Boolean) {
        ui.addView(chrome.row().apply {
            addView(chrome.key("", weight = 0.84f, style = Key.UTILITY, icon = Icon.GLOBE, description = "切换输入法") {
                getSystemService(InputMethodManager::class.java).showInputMethodPicker()
            })
            addView(chrome.key(if (numbers) "ABC" else "123", weight = 1f, style = Key.UTILITY, size = 13f) {
                if (finishComposition()) {
                    numbers = !numbers
                    render()
                }
            })
            if (!numbers && !secure) {
                addView(chrome.key(if (chinese) "中 / 英" else "英 / 中", weight = 1.16f,
                    style = Key.UTILITY, size = 12f, description = "切换中英文") {
                    if (finishComposition()) {
                        chinese = !chinese
                        keyboardPrefs.edit().putBoolean("chinese", chinese).apply()
                        render()
                    }
                })
            }
            addView(chrome.key("空格", weight = 3.2f, size = 13f) {
                if (spelling.isNotEmpty()) finishComposition() else commit(" ")
            })
            if (!numbers && !useNine) {
                val symbol = if (chinese && !secure) "。" else "."
                addView(chrome.key(symbol, weight = 0.72f, style = Key.UTILITY) { typePunctuation(symbol) })
            }
            addView(chrome.key("", weight = 1.18f, style = Key.TINT, icon = Icon.ENTER, description = "换行") {
                if (finishComposition()) commit("\n")
            })
        })
    }

    private fun typePunctuation(symbol: String) {
        if (finishComposition()) commit(symbol)
    }

    private fun updateCandidates() {
        val strip = candidateRow ?: return
        strip.removeAllViews()
        words = lexicon?.candidates(spelling, nine).orEmpty()
        if (spelling.isEmpty()) {
            val hint = when {
                lexiconFailed -> "词库未加载"
                lexicon == null -> "正在加载词库"
                nine -> "九键拼音"
                else -> "全键拼音"
            }
            strip.addView(chrome.text(hint, 12f, chrome.secondary).apply {
                setPadding(chrome.dp(5), 0, chrome.dp(5), 0)
            })
            return
        }
        // Keep the spelling selectable without giving it the visual weight of a real candidate.
        val raw = spelling
        strip.addView(chrome.key(raw, weight = 0f, height = 38, style = Key.QUIET, size = 12f) {
            insertCandidate(raw)
        }.apply {
            setTextColor(chrome.secondary)
            ellipsize = TextUtils.TruncateAt.END
            maxWidth = chrome.dp(84)
        })
        words.forEachIndexed { index, word ->
            strip.addView(chrome.key(word, weight = 0f, height = 38,
                style = if (index == 0) Key.TINT else Key.QUIET, size = 18f) { insertCandidate(word) })
        }
        (strip.parent as? HorizontalScrollView)?.scrollTo(0, 0)
    }

    private fun finishComposition(): Boolean =
        spelling.isEmpty() || insertCandidate(words.firstOrNull() ?: spelling)

    private fun insertCandidate(word: String): Boolean {
        if (!commit(word)) return false
        spelling = ""
        updateCandidates()
        return true
    }

    private fun commit(value: String): Boolean = viewActive && editor == currentEditor() &&
        currentInputConnection?.commitText(value, 1) == true

    private fun erase() {
        if (spelling.isNotEmpty()) {
            spelling = spelling.dropLast(1)
            updateCandidates()
        } else if (viewActive && editor == currentEditor()) {
            currentInputConnection?.let {
                if (!it.deleteSurroundingTextInCodePoints(1, 0)) it.deleteSurroundingText(1, 0)
            }
        }
    }

    private companion object {
        val NINE_LABELS = listOf("ABC", "DEF", "GHI", "JKL", "MNO", "PQRS", "TUV", "WXYZ")
        val NINE_PUNCTUATION = listOf("，", "。", "？")
    }
}
