package com.supportsoftware.checkerpro.firebase

import com.brian.base_iap.utils.FirebaseRemoteConfigUtil
import com.brian.base_iap.utils.IAPUtils
import com.supportsoftware.checkerpro.BuildConfig

/**
 * Facade Remote Config của app — ỦY QUYỀN sang [FirebaseRemoteConfigUtil] của lib.
 *
 * QUAN TRỌNG (spec §8.5):
 *  - KHÔNG subclass FirebaseRemoteConfigUtil (sẽ tạo singleton song song, default rỗng).
 *  - KHÔNG gọi FirebaseRemoteConfig.setDefaultsAsync trực tiếp (sẽ xoá `ads_config` của lib).
 *  - Ad unit nằm dưới 1 key `ads_config`; đọc qua getAdsConfigValue(placement).
 *  - Lib tự fetch trong BaseApplication.onCreate(); fetchAndActivate() ở đây chỉ để refresh + tính cache.
 */
class Remote private constructor() {

    private val frc get() = FirebaseRemoteConfigUtil.getInstance()

    fun fetchAndActivate(onComplete: (() -> Unit)? = null) {
        frc.fetchRemoteConfig { _ ->
            onComplete?.invoke()
        }
    }

    /** Ad unit id cho 1 placement (đọc key `ads_config`, fallback default_ads_config.json).
     *  DEBUG → unit TEST Google (luôn fill) để nghiệm thu UI ads (giống RN __DEV__); release → unit thật.
     *  Unit thật của app CHƯA publish thường NO_FILL (AdMob error code 3). */
    fun adUnit(placement: String): String =
        if (BuildConfig.DEBUG) debugTestUnit(placement) else frc.getAdsConfigValue(placement)

    private fun debugTestUnit(placement: String): String = when {
        placement.startsWith("inter") -> "ca-app-pub-3940256099942544/1033173712"   // test interstitial
        placement.startsWith("open") || placement.contains("app_open") ->
            "ca-app-pub-3940256099942544/9257395921"                                 // test app-open
        else -> "ca-app-pub-3940256099942544/2247696110"                             // test native
    }

    /** Đọc string: ưu tiên ads_config (nếu key là placement), fallback getString thường. */
    fun getString(key: String): String {
        val adValue = frc.getAdsConfigValue(key)
        return if (adValue.isNotEmpty()) adValue else frc.getString(key)
    }

    fun getBoolean(key: String): Boolean {
        // Premium override: cờ *_enable → false khi đã mua (ẩn ad cho user trả phí).
        if (IAPUtils.isPremium() && key.endsWith("_enable")) return false
        return frc.getBoolean(key)
    }

    fun getInt(key: String): Int = frc.getLong(key).toInt()
    fun getLong(key: String): Long = frc.getLong(key)

    /** Có hiển thị 1 placement không (xét premium + cờ *_enable). */
    fun isAdEnabled(placement: String): Boolean = getBoolean("${placement}_enable")

    companion object {
        @JvmStatic
        val instance: Remote by lazy { Remote() }
    }
}
