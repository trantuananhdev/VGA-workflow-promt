package com.supportsoftware.checkerpro.platform

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import android.util.Log
import com.brian.base_iap.utils.NativeCodecSnowFlakeCortexAI

/**
 * Mở màn IAP/paywall của SDK lib.
 *
 * Dùng thẳng màn IAP của LIB: nativeAiStartIapActivity → mở IapActivity (tự đóng sau khi mua).
 * Tiêu đề lấy từ getAppNameRes() của MyApplication.
 */
object IapLauncher {
    fun open(context: Context) {
        val activity = context.findActivity()
        if (activity == null) {
            Log.w("IapLauncher", "no Activity to open IAP")
            return
        }
        NativeCodecSnowFlakeCortexAI.nativeAiStartIapActivity(activity)
    }

    private tailrec fun Context.findActivity(): Activity? = when (this) {
        is Activity -> this
        is ContextWrapper -> baseContext.findActivity()
        else -> null
    }
}
