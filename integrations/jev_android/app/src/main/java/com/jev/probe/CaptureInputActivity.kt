package com.jev.probe

import android.app.Activity
import android.content.Intent
import android.graphics.ImageDecoder
import android.media.projection.MediaProjectionConfig
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.jev.probe.capture.ocr.CaptureHandoff
import com.jev.probe.capture.ocr.ProjectionCaptureService
import com.jev.probe.capture.ocr.ScreenCapture
import kotlin.math.roundToInt

/** System UI for a single screenshot or a single user-selected image. */
class CaptureInputActivity : AppCompatActivity() {
    private val requestId get() = intent.getStringExtra(EXTRA_REQUEST) ?: ""
    private var handedOff = false

    private val projection = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        val id = requestId
        if (CaptureHandoff.get(id) == null) { finish(); return@registerForActivityResult }
        if (result.resultCode != Activity.RESULT_OK || result.data == null) {
            fail("已取消系统截屏授权")
        } else {
            runCatching {
                ContextCompat.startForegroundService(this, Intent(this, ProjectionCaptureService::class.java)
                    .putExtra(EXTRA_REQUEST, id).putExtra("grant", result.data)
                    .putExtra("resultCode", result.resultCode))
                handedOff = true
                finish()
            }.onFailure { fail("无法启动系统截屏，请检查截屏方式或重试") }
        }
    }

    private val imagePicker = registerForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        val id = requestId
        if (CaptureHandoff.get(id) == null) { finish(); return@registerForActivityResult }
        if (uri == null) {
            fail("已取消导入图片")
            return@registerForActivityResult
        }
        Thread {
            val result = try {
                val source = ImageDecoder.createSource(contentResolver, uri)
                val bitmap = ImageDecoder.decodeBitmap(source) { decoder, info, _ ->
                    val width = info.size.width
                    val height = info.size.height
                    val scale = (1600.0 / maxOf(width, height)).coerceAtMost(1.0)
                    decoder.allocator = ImageDecoder.ALLOCATOR_SOFTWARE
                    decoder.setTargetSize(
                        (width * scale).roundToInt().coerceAtLeast(1),
                        (height * scale).roundToInt().coerceAtLeast(1)
                    )
                }
                ScreenCapture.Result.Ok(bitmap, 1f, 1f)
            } catch (_: Exception) {
                ScreenCapture.Result.Failed(-10, "无法读取这张图片，请换一张重试")
            }
            runOnUiThread { deliver(id, result) }
        }.start()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (CaptureHandoff.get(requestId) == null) { finish(); return }
        if (savedInstanceState != null) return
        if (intent.getBooleanExtra(EXTRA_PICK_IMAGE, false)) {
            runCatching { imagePicker.launch("image/*") }
                .onFailure { fail("无法打开图片选择器，请重试") }
            return
        }
        runCatching {
            val manager = getSystemService(MediaProjectionManager::class.java)
            val consent = if (Build.VERSION.SDK_INT >= 34)
                manager.createScreenCaptureIntent(MediaProjectionConfig.createConfigForDefaultDisplay())
            else manager.createScreenCaptureIntent()
            projection.launch(consent)
        }.onFailure { fail("无法打开系统入口，请返回聊天后重试") }
    }

    private fun fail(message: String) {
        deliver(requestId, ScreenCapture.Result.Failed(-10, message))
    }

    private fun deliver(id: String, result: ScreenCapture.Result) {
        handedOff = true
        finish()
        Handler(Looper.getMainLooper()).postDelayed({ CaptureHandoff.complete(id, result) }, 200)
    }

    override fun onDestroy() {
        super.onDestroy()
        if (isFinishing && !handedOff) CaptureHandoff.cancel(requestId)
    }

    companion object {
        const val EXTRA_REQUEST = "captureRequest"
        const val EXTRA_PICK_IMAGE = "pickImage"
    }
}
