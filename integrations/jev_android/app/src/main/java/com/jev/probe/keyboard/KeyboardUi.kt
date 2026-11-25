package com.jev.probe.keyboard

import android.content.Context
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.Canvas
import android.graphics.ColorFilter
import android.graphics.Paint
import android.graphics.PixelFormat
import android.graphics.Typeface
import android.graphics.drawable.Drawable
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.RippleDrawable
import android.text.SpannableString
import android.text.style.DynamicDrawableSpan
import android.text.style.ImageSpan
import android.view.Gravity
import android.view.View
import android.widget.LinearLayout
import android.widget.TextView
import com.jev.probe.R
import kotlin.math.roundToInt

/** The keyboard uses the warm palette from the iOS app, adjusted for a dense layout. */
internal class KeyboardUi(private val context: Context) {
    private val dark get() = (context.resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK) ==
        Configuration.UI_MODE_NIGHT_YES
    private fun tone(light: Long, night: Long) = (if (dark) night else light).toInt()

    val base get() = tone(0xFFECE3DA, 0xFF251D19)
    val panel get() = tone(0xFFFFF8F0, 0xFF271F1A)
    val paper get() = tone(0xFFFFFDFA, 0xFF372C25)
    val muted get() = tone(0xFFF3EBE2, 0xFF322720)
    val keyUtility get() = tone(0xFFE0D2C4, 0xFF493B31)
    val line get() = tone(0xFFE3D3C4, 0xFF564439)
    val ink get() = tone(0xFF392820, 0xFFF7E9DE)
    val secondary get() = tone(0xFF6D5547, 0xFFCCB7A6)
    val accent get() = tone(0xFF884421, 0xFFF5B78C)
    val tint get() = tone(0xFFF6E2D1, 0xFF483225)
    val onAccent get() = tone(0xFFFFF9F0, 0xFF302017)

    enum class Key { LETTER, UTILITY, PRIMARY, QUIET, TINT }
    enum class Icon { GLOBE, BACK, REMOVE, BACKSPACE, ENTER, CAPTURE, IMAGE }

    fun row() = LinearLayout(context).apply {
        orientation = LinearLayout.HORIZONTAL
        isBaselineAligned = false
    }
    fun column() = LinearLayout(context).apply { orientation = LinearLayout.VERTICAL }
    fun dp(value: Int) = (value * context.resources.displayMetrics.density).roundToInt()

    fun padded(view: View, horizontal: Int, vertical: Int) {
        view.setPadding(dp(horizontal), dp(vertical), dp(horizontal), dp(vertical))
    }

    fun shape(fill: Int, radius: Int, stroke: Int? = null) = GradientDrawable().apply {
        cornerRadius = dp(radius).toFloat()
        setColor(fill)
        stroke?.let { setStroke(dp(1), it) }
    }

    fun touch(fill: Int, radius: Int, stroke: Int? = null) = RippleDrawable(
        ColorStateList.valueOf(tone(0x2270442D, 0x33EDAD7B)),
        shape(fill, radius, stroke),
        null
    )

    fun text(value: CharSequence, size: Float, color: Int = ink, weight: Int = 400) =
        TextView(context).apply {
            text = value
            textSize = size
            setTextColor(color)
            typeface = Typeface.create(Typeface.DEFAULT, weight, false)
            includeFontPadding = false
        }

    fun key(
        value: CharSequence, weight: Float = 1f, height: Int = 44, style: Key = Key.LETTER,
        size: Float = 15f, icon: Icon? = null, description: String? = null, onClick: (() -> Unit)? = null
    ): TextView {
        val fill = when (style) {
            Key.LETTER -> paper
            Key.UTILITY -> keyUtility
            Key.PRIMARY -> accent
            Key.QUIET -> panel
            Key.TINT -> tint
        }
        val color = when (style) {
            Key.PRIMARY -> onAccent
            Key.TINT -> accent
            else -> ink
        }
        return text(value, size, color, if (style == Key.LETTER) 500 else 600).apply {
            gravity = Gravity.CENTER
            setPadding(dp(3), 0, dp(3), 0)
            setSingleLine()
            if (weight == 0f) minimumWidth = dp(44)
            val border = if (style == Key.LETTER) line else null
            background = touch(fill, if (style == Key.LETTER) 8 else 10, border)
            layoutParams = LinearLayout.LayoutParams(if (weight == 0f) -2 else 0, dp(height), weight).apply {
                setMargins(dp(2), dp(2), dp(2), dp(2))
            }
            if (icon != null) text = inlineGlyph(icon, color, size = 20)
            contentDescription = description
            if (onClick != null) setOnClickListener { onClick() }
        }
    }

    fun inlineGlyph(icon: Icon, color: Int, size: Int): CharSequence = SpannableString(" ").apply {
        setSpan(ImageSpan(glyph(icon, color, size), DynamicDrawableSpan.ALIGN_CENTER), 0, length, 0)
    }

    fun glyph(icon: Icon, color: Int = ink, size: Int = 20): Drawable =
        KeyboardGlyph(icon, color).apply { setBounds(0, 0, dp(size), dp(size)) }

    fun mascot(size: Int): Drawable = requireNotNull(context.getDrawable(R.drawable.shiba_mascot)).apply {
        setBounds(0, 0, dp(size), dp(size))
    }
}

private class KeyboardGlyph(private val icon: KeyboardUi.Icon, color: Int) : Drawable() {
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        this.color = color
        style = Paint.Style.STROKE
        strokeWidth = 1.6f
        strokeCap = Paint.Cap.ROUND
        strokeJoin = Paint.Join.ROUND
    }

    override fun draw(canvas: Canvas) {
        val checkpoint = canvas.save()
        canvas.translate(bounds.left.toFloat(), bounds.top.toFloat())
        canvas.scale(bounds.width() / 24f, bounds.height() / 24f)
        when (icon) {
            KeyboardUi.Icon.GLOBE -> {
                canvas.drawCircle(12f, 12f, 9f, paint)
                canvas.drawOval(8f, 3f, 16f, 21f, paint)
                canvas.drawLine(3.4f, 12f, 20.6f, 12f, paint)
            }
            KeyboardUi.Icon.BACK -> {
                stroke(canvas, 11f, 5f, 4f, 12f, 11f, 19f)
                canvas.drawLine(4f, 12f, 20f, 12f, paint)
            }
            KeyboardUi.Icon.REMOVE -> {
                stroke(canvas, 6f, 6f, 18f, 18f)
                stroke(canvas, 18f, 6f, 6f, 18f)
            }
            KeyboardUi.Icon.BACKSPACE -> {
                stroke(canvas, 2f, 12f, 8f, 5f, 21f, 5f, 21f, 19f, 8f, 19f, 2f, 12f)
                stroke(canvas, 11f, 9f, 17f, 15f)
                stroke(canvas, 17f, 9f, 11f, 15f)
            }
            KeyboardUi.Icon.ENTER -> {
                stroke(canvas, 20f, 5f, 20f, 14f, 5f, 14f)
                stroke(canvas, 10f, 9f, 5f, 14f, 10f, 19f)
            }
            KeyboardUi.Icon.CAPTURE -> {
                stroke(canvas, 8f, 3f, 3f, 3f, 3f, 8f)
                stroke(canvas, 16f, 3f, 21f, 3f, 21f, 8f)
                stroke(canvas, 3f, 16f, 3f, 21f, 8f, 21f)
                stroke(canvas, 16f, 21f, 21f, 21f, 21f, 16f)
                canvas.drawRect(7f, 8f, 17f, 16f, paint)
            }
            KeyboardUi.Icon.IMAGE -> {
                canvas.drawRoundRect(3f, 4f, 21f, 20f, 3f, 3f, paint)
                canvas.drawCircle(9f, 9f, 1.7f, paint)
                stroke(canvas, 5f, 17f, 12f, 12f, 18f, 17f)
            }
        }
        canvas.restoreToCount(checkpoint)
    }

    private fun stroke(canvas: Canvas, vararg points: Float) {
        for (index in 2 until points.size step 2) {
            canvas.drawLine(points[index - 2], points[index - 1], points[index], points[index + 1], paint)
        }
    }

    override fun setAlpha(alpha: Int) { paint.alpha = alpha; invalidateSelf() }
    override fun setColorFilter(filter: ColorFilter?) { paint.colorFilter = filter; invalidateSelf() }
    @Deprecated("Deprecated in Android") override fun getOpacity(): Int = PixelFormat.TRANSLUCENT
}
