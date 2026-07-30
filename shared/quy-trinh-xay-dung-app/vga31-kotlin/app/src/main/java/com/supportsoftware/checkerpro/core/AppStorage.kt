package com.supportsoftware.checkerpro.core

import android.content.Context

/**
 * Wrapper SharedPreferences "AppStorage" (cùng prefs MyApplication.notifyLanguageSaved ghi "language").
 * Quản lý first-open / onboarding (port các key AsyncStorage của RN: FIRST_LAUNCH, AGREE…).
 */
object AppStorage {

    private const val PREFS = "AppStorage"
    private const val KEY_FIRST_OPEN = "first_open"
    private const val KEY_ONBOARDING_DONE = "onboarding_done"
    private const val KEY_AGREE = "agree_permission"
    private const val KEY_LANGUAGE = "language"

    // Port RN: bộ đếm số lần vào Home (goToHomeNumber, bắt đầu 1, +1 mỗi lần mở app đến Home).
    private const val KEY_GO_TO_HOME = "go_to_home_number"
    // Nguồn cài (InstallReferrer): true = từ chiến dịch quảng cáo. Cache 1 lần (không đổi).
    private const val KEY_ADS_CAMPAIGN = "is_ads_campaign"
    private const val KEY_ADS_CAMPAIGN_RESOLVED = "ads_campaign_resolved"

    private fun prefs(context: Context) =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    fun isFirstOpen(context: Context): Boolean =
        prefs(context).getBoolean(KEY_FIRST_OPEN, true)

    fun isOnboardingDone(context: Context): Boolean =
        prefs(context).getBoolean(KEY_ONBOARDING_DONE, false)

    fun setOnboardingDone(context: Context, done: Boolean = true) {
        prefs(context).edit()
            .putBoolean(KEY_ONBOARDING_DONE, done)
            .putBoolean(KEY_FIRST_OPEN, false)
            .apply()
    }

    fun hasAgreedPermissions(context: Context): Boolean =
        prefs(context).getBoolean(KEY_AGREE, false)

    fun setAgreedPermissions(context: Context) {
        prefs(context).edit().putBoolean(KEY_AGREE, true).apply()
    }

    fun language(context: Context): String? =
        prefs(context).getString(KEY_LANGUAGE, null)

    // ── Gate hiện Intro (port RN AppNavigation.js) ────────────────────────────

    /** Lần mở hiện tại (goToHomeNumber). Mặc định 1 = lần đầu. */
    fun goToHomeNumber(context: Context): Int =
        prefs(context).getInt(KEY_GO_TO_HOME, 1)

    fun setGoToHomeNumber(context: Context, n: Int) {
        prefs(context).edit().putInt(KEY_GO_TO_HOME, n).apply()
    }

    /** Đã cache kết quả InstallReferrer chưa. */
    fun isAdsCampaignResolved(context: Context): Boolean =
        prefs(context).getBoolean(KEY_ADS_CAMPAIGN_RESOLVED, false)

    /** true = install từ chiến dịch ads. Fallback = true (giống RN: mọi nhánh lỗi coi như ads). */
    fun isAdsCampaign(context: Context): Boolean =
        prefs(context).getBoolean(KEY_ADS_CAMPAIGN, true)

    fun setAdsCampaign(context: Context, isAds: Boolean) {
        prefs(context).edit()
            .putBoolean(KEY_ADS_CAMPAIGN, isAds)
            .putBoolean(KEY_ADS_CAMPAIGN_RESOLVED, true)
            .apply()
    }
}
