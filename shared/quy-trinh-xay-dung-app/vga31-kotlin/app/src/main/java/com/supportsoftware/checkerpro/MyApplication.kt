package com.supportsoftware.checkerpro

import android.app.Activity
import com.supportsoftware.checkerpro.core.InstallReferrerHelper
import com.supportsoftware.checkerpro.core.LocaleHelper
import com.supportsoftware.checkerpro.core.MainActivity
import com.supportsoftware.checkerpro.firebase.Remote
import com.brian.base_application.BaseApplication
import com.brian.base_iap.utils.FirebaseRemoteConfigUtil
import com.brian.base_iap.utils.IAPUtils
import com.nlbn.ads.util.AppFlyer
import dagger.hilt.android.HiltAndroidApp

/**
 * Application host — kế thừa [BaseApplication] của thư viện base-application.
 * Khai báo trong AndroidManifest: <application android:name=".MyApplication" ... />
 *
 * LƯU Ý:
 *  - PHẢI gọi super.onCreate() (lib làm toàn bộ init ads/consent/IAP/notification trong đó).
 *  - KHÔNG tự init MobileAds / consent / AppsFlyer ở nơi khác — lib lo (AppsFlyer init tại initAppFlyerId()).
 *
 * TODO trước phát hành:
 *  - public_license_key: thay key Play Console THẬT của com.supportsoftware.checkerpro.
 *  - facebook_app_id / facebook_client_token: điền giá trị thật.
 *  - Thay drawable placeholder (logo) cho icon splash / notification / preview bằng ảnh đúng kích thước.
 */
@HiltAndroidApp
class MyApplication : BaseApplication() {

    override fun onCreate() {
        super.onCreate()   // lib init ads/consent/IAP/notification + set default `ads_config` + tự fetch RC

        // Đăng ký default Remote Config của app (KHÔNG gọi setDefaultsAsync trực tiếp — sẽ xoá `ads_config`).
        FirebaseRemoteConfigUtil.getInstance().setAppDefaultsFromXml(R.xml.config)

        // Tính cache + fetch lại (lib đã tự fetch RC trong super.onCreate()).
        Remote.instance.fetchAndActivate()

        // Xác định nguồn cài (InstallReferrer) SỚM để kịp cache trước khi lib mở Home
        // → MainActivity.resolveStartRoute gate màn Intro theo ads/organic (port RN).
        InstallReferrerHelper.resolve(this)
    }

    // ===================== Thương hiệu & Splash =====================
    override fun getAppNameRes(): Int = R.string.app_name
    override fun getIconSplashRes(): Int = R.drawable.logo            // TODO: icon splash riêng
    override fun getSplashLoadingRes(): Int = R.raw.splash_loading

    // ===================== Định tuyến =====================
    override fun getHomeActivity(): Class<out Activity> = MainActivity::class.java

    // ===================== Năng lực =====================
    override fun hasForegroundServicePermission(): Boolean = true

    // ===================== Khởi tạo =====================
    override fun initAppFlyerId() {
        AppFlyer.getInstance().initAppFlyer(
            this,
            getString(R.string.app_flyer_id),
            /* enableLog       */ BuildConfig.DEBUG,
            /* enableDeepLink  */ false,
            /* enableUninstall */ true,
        )
    }

    override fun setupKoin() { /* app không dùng Koin */ }

    // ===================== Ngôn ngữ =====================
    // App đọc ngôn ngữ từ prefs "AppStorage" key "language".
    // QUAN TRỌNG: lib gọi hàm này khi user chọn ngôn ngữ (cả màn Language lần đầu LẪN màn Language
    // mở từ Settings). MainActivity là AppCompat/Compose không tự áp locale của lib → phải set
    // per-app locale của AndroidX để AppCompat recreate MainActivity theo ngôn ngữ mới
    // (nếu không, đổi ngôn ngữ trong Settings sẽ không đổi chuỗi các màn app).
    override fun notifyLanguageSaved(languageCode: String) {
        getSharedPreferences("AppStorage", MODE_PRIVATE).edit()
            .putString("language", languageCode).apply()
        LocaleHelper.updateLocale(this, languageCode)
    }

    // ===================== Khoá IAP (product id Play Console) =====================
    // GHI CHÚ: lấy từ RN utils_app/envApp.js —
    //   SUBSCRIPTION_IDS[0] → iapPremiumKey ; BASE_PLAN_MONTH → Monthly ; BASE_PLAN_YEAR → Yearly.
    //   envApp KHÔNG có base-plan tuần → Weekly để mặc định "weekly".
    // vga31b: SUBSCRIPTION_IDS = ['premium_remove_all_ads'], monthly, yearly.
 override fun iapPremiumKey(): String = "release_premium_access"   // product id (KEY_PREMIUM)
    override fun iapPremiumWeeklyKey(): String = "release-weekly-plan"
    override fun iapPremiumMonthlyKey(): String = "release-monthly-plan"
    override fun iapPremiumYearlyKey(): String = "release-yearly-plan"
    override fun iapPublicKey(): String = getString(R.string.public_license_key)

    // ===================== Bộ thông báo (5 phần tử, khớp index) =====================
    override fun getNotificationImages(): IntArray = intArrayOf(
        R.drawable.logo, R.drawable.logo, R.drawable.logo, R.drawable.logo, R.drawable.logo,
    )
    override fun getNotificationTitles2ArrayRes(): Int = R.array.notification_title2
    override fun getNotificationMessages2ArrayRes(): Int = R.array.notification_message2
    override fun getNotificationButtons2ArrayRes(): Int = R.array.notification_button2

    override fun getNotificationIconRes(): Int = R.drawable.logo      // TODO: icon status-bar 24dp alpha
    override fun getNotificationChannelPrefix(): String = "SoftwareUpdate"

    override fun getNewFileNotiContentRes(): Int = R.string.baseapp_new_file_content
    override fun getScreenshotNotiTitleRes(): Int = R.string.baseapp_screenshot_title
    override fun getRecentDocumentsTitleRes(): Int = R.string.baseapp_recent_title
    override fun getOpenTextRes(): Int = R.string.baseapp_open
    override fun getScanDocumentRes(): Int = R.string.baseapp_scan
    override fun getWidgetButtonBackgroundRes(): Int = R.drawable.notification_button_bg
    override fun getDailyCallOpenAppContentRes(): Int = R.string.baseapp_daily_open_content
    override fun getCheckNowTextRes(): Int = R.string.baseapp_check_now
    override fun getDocumentPreviewRes(): Int = R.drawable.logo        // TODO: ảnh 365x174dp
    override fun getFullScreenNoti1Res(): Int = R.string.baseapp_fullscreen_1
    override fun getFullScreenNoti2Res(): Int = R.string.baseapp_fullscreen_2
    override fun getNotificationOutAppTitleRes(): Int = R.string.baseapp_outapp_title
    override fun getNotificationOutAppContentRes(): Int = R.string.baseapp_outapp_content

    // Dialog xin quyền thông báo
    override fun getNotiTitleRes(): Int = R.string.baseapp_noti_title
    override fun getNotiContentRes(): Int = R.string.baseapp_noti_content

    // ===================== Tính năng màn IAP (icon + text đi cặp) =====================
    override fun getFeature1IconRes(): Int = R.drawable.crown
    override fun getFeature2IconRes(): Int = R.drawable.ic_star
    override fun getFeature3IconRes(): Int = R.drawable.ic_subscription
    override fun getFeature4IconRes(): Int = R.drawable.ic_music
    override fun getFeature5IconRes(): Int = R.drawable.ic_settings

    override fun getFeature1TextRes(): Int? = R.string.baseapp_feature1
    override fun getFeature2TextRes(): Int? = R.string.baseapp_feature2
    override fun getFeature3TextRes(): Int? = R.string.baseapp_feature3
    override fun getFeature4TextRes(): Int? = R.string.baseapp_feature4
    override fun getFeature5TextRes(): Int? = R.string.baseapp_feature5

    // ===================== Cấu hình quảng cáo =====================
    override fun isPurchased(): Boolean = IAPUtils.isPremium()
    override fun enableAdsResume(): Boolean = !IAPUtils.isPremium()
    override fun buildDebug(): Boolean = BuildConfig.DEBUG
    override fun getListTestDeviceId(): MutableList<String> = mutableListOf()
}
