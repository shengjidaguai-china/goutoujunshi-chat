package com.jev.probe.keyboard

import android.content.Context
import android.content.res.ColorStateList
import android.graphics.Bitmap
import android.view.Gravity
import android.view.View
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.ScrollView
import com.jev.probe.core.Analysis
import com.jev.probe.core.RankedReply
import com.jev.probe.keyboard.KeyboardUi.Icon
import com.jev.probe.keyboard.KeyboardUi.Key
import kotlin.math.roundToInt

internal class KeyboardAssistantPanel(private val context: Context, private val ui: KeyboardUi) {
    fun header(parent: LinearLayout, title: String, back: (() -> Unit)?, typing: () -> Unit) {
        parent.addView(ui.row().apply {
            gravity = Gravity.CENTER_VERTICAL
            if (back != null) {
                addView(ui.key("", weight = 0f, height = 40, style = Key.QUIET,
                    icon = Icon.BACK, description = "返回取图") { back() })
            }
            addView(ui.text(title, 19f, weight = 700).apply {
                if (back == null) {
                    setPadding(ui.dp(7), 0, 0, 0)
                    setCompoundDrawablesRelative(ui.mascot(26), null, null, null)
                    compoundDrawablePadding = ui.dp(8)
                }
                isAccessibilityHeading = true
            }, LinearLayout.LayoutParams(0, -2, 1f))
            addView(ui.key("打字", weight = 0f, height = 40, style = Key.QUIET, size = 13f, onClick = typing))
        })
    }

    fun menu(parent: LinearLayout, capture: () -> Unit, pick: () -> Unit) {
        parent.addView(ui.row().apply {
            addView(imageAction("截图识别", Icon.CAPTURE, true, capture))
            addView(imageAction("导入图片识别", Icon.IMAGE, false, pick))
        })
    }

    private fun imageAction(title: String, icon: Icon, primary: Boolean, action: () -> Unit) =
        ui.column().apply {
            val color = if (primary) ui.onAccent else ui.ink
            background = ui.touch(if (primary) ui.accent else ui.paper, 14, if (primary) null else ui.line)
            ui.padded(this, 13, 13)
            layoutParams = LinearLayout.LayoutParams(0, -2, 1f).apply {
                setMargins(ui.dp(4), ui.dp(4), ui.dp(4), ui.dp(5))
            }
            addView(ImageView(context).apply { setImageDrawable(ui.glyph(icon, color, 24)) }, ui.dp(24), ui.dp(24))
            addView(ui.text(title, 14f, color, 650).apply { setPadding(0, ui.dp(9), 0, 0) })
            isFocusable = true
            contentDescription = title
            setOnClickListener { action() }
        }

    fun notice(parent: LinearLayout, message: String, busy: Boolean = false) {
        parent.addView(ui.row().apply {
            ui.padded(this, 12, 14)
            gravity = Gravity.CENTER_VERTICAL
            if (busy) {
                addView(ProgressBar(context).apply {
                    indeterminateTintList = ColorStateList.valueOf(ui.accent)
                }, LinearLayout.LayoutParams(ui.dp(18), ui.dp(18)).apply { marginEnd = ui.dp(10) })
            }
            addView(ui.text(message, 13f, ui.secondary), LinearLayout.LayoutParams(0, -2, 1f))
        })
    }

    fun preview(parent: LinearLayout, bitmap: Bitmap, cloudHost: String?, recognize: () -> Unit) {
        parent.addView(ImageView(context).apply {
            setImageBitmap(bitmap)
            scaleType = ImageView.ScaleType.FIT_CENTER
            background = ui.shape(ui.muted, 14, ui.line)
            ui.padded(this, 8, 8)
            contentDescription = "本轮图片预览"
        }, LinearLayout.LayoutParams(-1, ui.dp(panelHeight(0.22f, 98, 190))).apply {
            setMargins(ui.dp(4), ui.dp(4), ui.dp(4), 0)
        })
        notice(parent, if (cloudHost != null) "图片将发送至 ${cloudHost.ifBlank { "已配置的视觉接口" }}" else "ML Kit 本地识图")
        footer(parent, ui.key(if (cloudHost != null) "发送图片并识别" else "识别文字", style = Key.PRIMARY, onClick = recognize))
    }

    fun review(parent: LinearLayout, transcript: List<TranscriptLine>, analyze: () -> Unit) {
        val count = ui.text("", 12f, ui.accent, 600)
        val submit = ui.key("确认并生成回复", style = Key.PRIMARY, onClick = analyze)
        fun refreshCount() {
            val included = transcript.count { it.included }
            count.text = "保留 $included 条"
            submit.isEnabled = included > 0
            submit.alpha = if (included > 0) 1f else 0.5f
        }
        parent.addView(ui.row().apply {
            gravity = Gravity.CENTER_VERTICAL
            ui.padded(this, 10, 5)
            addView(ui.text("核对文字，点称呼可换说话人", 12f, ui.secondary),
                LinearLayout.LayoutParams(0, -2, 1f))
            addView(count)
        })
        scroll(parent, panelHeight(0.30f, 112, 256)) {
            transcript.sortedBy { !it.included }.forEach { line ->
                addView(messageBubble(line, ::refreshCount))
            }
        }
        footer(parent, submit)
        refreshCount()
    }

    private fun messageBubble(line: TranscriptLine, onInclusionChanged: () -> Unit): LinearLayout {
        val card = ui.column()
        val label = ui.text(line.text, 15f).apply {
            setLineSpacing(ui.dp(3).toFloat(), 1f)
            setPadding(ui.dp(9), 0, ui.dp(9), ui.dp(9))
        }
        val speaker = ui.key("", weight = 0f, height = 34, style = Key.QUIET, size = 12f)
        val exclusion = ui.key("", weight = 0f, height = 34, style = Key.QUIET, size = 12f)
        card.addView(ui.row().apply {
            gravity = Gravity.CENTER_VERTICAL
            addView(speaker)
            addView(View(context), LinearLayout.LayoutParams(0, 1, 1f))
            addView(exclusion)
        })
        card.addView(label)
        fun refreshBubble() {
            val mine = line.side == "me"
            val fill = when {
                !line.included -> ui.muted
                mine -> ui.tint
                else -> ui.paper
            }
            val role = if (mine) "我" else "对方"
            card.background = ui.shape(fill, 13, if (mine && line.included) null else ui.line)
            card.layoutParams = LinearLayout.LayoutParams(-1, -2).apply {
                setMargins(ui.dp(if (mine) 34 else 4), ui.dp(3),
                    ui.dp(if (mine) 4 else 34), ui.dp(4))
            }
            speaker.text = "$role ⇄"
            speaker.contentDescription = "当前说话人$role，点按切换"
            speaker.setTextColor(ui.accent)
            speaker.background = ui.touch(fill, 10)
            exclusion.text = if (line.included) ui.inlineGlyph(Icon.REMOVE, ui.secondary, 16) else "恢复"
            exclusion.contentDescription = if (line.included) "排除这条消息" else "恢复这条消息"
            exclusion.setTextColor(ui.secondary)
            exclusion.background = ui.touch(fill, 10)
            label.setTextColor(if (line.included) ui.ink else ui.secondary)
        }
        speaker.setOnClickListener {
            line.side = if (line.side == "me") "other" else "me"
            refreshBubble()
        }
        exclusion.setOnClickListener {
            line.included = !line.included
            refreshBubble()
            onInclusionChanged()
        }
        refreshBubble()
        return card
    }

    fun results(parent: LinearLayout, result: Analysis, fill: (RankedReply) -> Unit) {
        scroll(parent, panelHeight(0.36f, 154, 326)) {
            val intent = result.trueIntent?.choice.orEmpty()
            val strategy = result.strategy ?: result.bestAction?.choice.orEmpty()
            if (intent.isNotBlank() || strategy.isNotBlank()) {
                addView(card(ui.muted).apply {
                    addView(ui.row().apply {
                        if (intent.isNotBlank()) addView(ui.text("可能的意图", 12f, ui.secondary, 600),
                            LinearLayout.LayoutParams(0, -2, 1f))
                        if (strategy.isNotBlank()) addView(ui.text("建议 · $strategy", 12f, ui.accent, 650))
                    })
                    if (intent.isNotBlank()) addView(ui.text(intent, 15f).apply {
                        setPadding(0, ui.dp(6), 0, 0)
                        setLineSpacing(ui.dp(2).toFloat(), 1f)
                    })
                })
            }
            result.rankedReplies.forEachIndexed { index, reply ->
                addView(replyCard(reply, index, result.rankedReplies.size) { fill(reply) })
            }
            if (result.rankedReplies.isEmpty()) notice(this, "本轮没有可填入的候选")
        }
    }

    private fun replyCard(reply: RankedReply, index: Int, count: Int, fill: () -> Unit) =
        card(if (index == 0) ui.tint else ui.paper).apply {
            val title = if (count == 1) "建议回复" else if (index == 0) "首选回复" else "候选 ${index + 1}"
            val weight = if (reply.prob > 0) " · ${(reply.prob * 100).roundToInt()}% 推荐权重" else ""
            addView(ui.text(title + weight, 12f, ui.accent, 650))
            addView(ui.text(reply.text, 16f, weight = 500).apply {
                setPadding(0, ui.dp(7), 0, ui.dp(4))
                setLineSpacing(ui.dp(2).toFloat(), 1f)
            })
            addView(ui.key("填入草稿", weight = 0f, height = 39,
                style = if (index == 0) Key.PRIMARY else Key.UTILITY, size = 13f, onClick = fill).apply {
                setPadding(ui.dp(12), 0, ui.dp(12), 0)
                layoutParams = LinearLayout.LayoutParams(-2, ui.dp(39)).apply { gravity = Gravity.END }
            })
        }

    private fun card(fill: Int) = ui.column().apply {
        background = ui.shape(fill, 14, ui.line)
        ui.padded(this, 12, 10)
        layoutParams = LinearLayout.LayoutParams(-1, -2).apply {
            setMargins(ui.dp(4), ui.dp(3), ui.dp(4), ui.dp(5))
        }
    }

    private fun footer(parent: LinearLayout, action: View) {
        parent.addView(ui.row().apply {
            setPadding(ui.dp(2), ui.dp(4), ui.dp(2), ui.dp(2))
            addView(action)
        })
    }

    private fun scroll(parent: LinearLayout, height: Int, content: LinearLayout.() -> Unit) {
        parent.addView(ScrollView(context).apply {
            overScrollMode = View.OVER_SCROLL_IF_CONTENT_SCROLLS
            addView(ui.column().apply(content))
        }, -1, ui.dp(height))
    }

    private fun panelHeight(fraction: Float, minimum: Int, maximum: Int) =
        (context.resources.configuration.screenHeightDp * fraction).roundToInt().coerceIn(minimum, maximum)
}
