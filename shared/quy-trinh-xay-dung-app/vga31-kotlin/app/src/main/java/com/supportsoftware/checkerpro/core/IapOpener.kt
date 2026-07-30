package com.supportsoftware.checkerpro.core

import android.content.Context
import com.brian.base_iap.utils.IAPUtils
import com.supportsoftware.checkerpro.platform.IapLauncher

/**
 * Mở màn IAP/paywall của lib. Dùng IapLauncher để lấy tiêu đề từ app name.
 * Dùng cho nút mua gói ở Home/Settings và paywall-gate tính năng premium.
 */
object IapOpener {

    fun open(context: Context, source: String = "home") {
        IapLauncher.open(context)
    }

    /** Paywall-gate: nếu đã premium chạy [onPremium], chưa thì mở IAP (tự đóng sau khi mua). */
    fun gate(context: Context, source: String = "feature", onPremium: () -> Unit) {
        if (IAPUtils.isPremium()) onPremium() else open(context, source)
    }
}
