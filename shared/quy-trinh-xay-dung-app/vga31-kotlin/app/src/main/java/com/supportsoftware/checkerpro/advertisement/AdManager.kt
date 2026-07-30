package com.supportsoftware.checkerpro.advertisement

import android.app.Activity
import com.supportsoftware.checkerpro.firebase.Remote
import com.brian.base_iap.utils.IAPUtils
import com.google.android.gms.ads.LoadAdError
import com.nlbn.ads.callback.AdCallback
import com.nlbn.ads.util.Admob

/**
 * Điều phối Interstitial (port kịch bản RN + mô hình InterFlow của vga23b):
 *  - inter thường: `<inter>_enable` + `<inter>_ratio` (showCount % ratio == 0) + `<inter>_max`/ngày.
 *  - NATIVE-INTER (native fullscreen `native_<inter>`) đóng vai "giả interstitial":
 *      • inter HIỆN  → khi inter ĐÓNG mới xét native-inter (2 quảng cáo liên tiếp - chain).
 *      • inter KHÔNG → xét native-inter ngay (fallback).
 *  - QUAN TRỌNG (#4): tần suất native-inter đánh giá SAU khi inter đóng (giống 23b InterFlow) → chỉ
 *    tăng đếm khi thực sự tới lượt, không lệch maxPerDay.
 *  - (#5) PRELOAD: nạp trước native-inter trong lúc inter đang hiển thị → đóng inter là hiện gần như tức thì.
 * [onNext] luôn gọi đúng 1 lần (sau khi cả 2 quảng cáo xong / bỏ qua).
 */
object AdManager {

    private const val TAG = "ADS"

    fun showInter(activity: Activity, interPlacement: String, onNext: () -> Unit) {
        val remote = Remote.instance
        if (IAPUtils.isPremium()) { onNext(); return }

        val ni = "native_$interPlacement" // inter_home → native_inter_home

        // Xét + hiện native-inter (đánh giá tần suất TẠI ĐÂY — sau khi inter đóng, hoặc khi inter không hiện).
        val proceedToNativeInter = {
            val niUnit = remote.adUnit(ni)
            val niShow = remote.isAdEnabled(ni) && niUnit.isNotBlank() &&
                AdScenario.shouldShow(
                    activity, ni,
                    ratio = remote.getInt("${ni}_ratio"),
                    maxPerDay = remote.getInt("${ni}_max"),
                )
            println(TAG + " " + "native-inter $ni → show=$niShow")
            if (niShow) NativeInterController.show(ni) { onNext() } else onNext()
        }

        val interAdUnit = remote.adUnit(interPlacement)
        val interShow = remote.isAdEnabled(interPlacement) && interAdUnit.isNotBlank() &&
            AdScenario.shouldShow(
                activity, interPlacement,
                ratio = remote.getInt("${interPlacement}_ratio"),
                maxPerDay = remote.getInt("${interPlacement}_max"),
            )
        println(TAG + " " + "showInter $interPlacement → interShow=$interShow")

        if (interShow) {
            // #5: preload native-inter NGAY (nếu bật) để sẵn sàng khi inter đóng.
            if (remote.isAdEnabled(ni)) NativeInterController.preload(activity.applicationContext, remote.adUnit(ni))
            var advanced = false
            fun once() { if (!advanced) { advanced = true; proceedToNativeInter() } }
            Admob.getInstance().loadAndShowInter(
                activity, interAdUnit, /* showLoading */ false,
                object : AdCallback() {
                    override fun onNextAction() {
                        println(TAG + " " + "inter $interPlacement closed → next")
                        once()
                    }

                    override fun onAdFailedToLoad(error: LoadAdError?) {
                        println(TAG + " ERR " + "inter $interPlacement LOAD FAILED: code=${error?.code} ${error?.message}")
                        once()
                    }
                },
            )
        } else {
            proceedToNativeInter()   // inter không hiện → native-inter ngay (fallback)
        }
    }
}
