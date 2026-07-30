package com.supportsoftware.checkerpro.ui.nav

/**
 * Toàn bộ route trong MainActivity (Compose NavHost).
 * Lib sở hữu Splash/Inter/Language-đầu/IAP; ở đây chỉ là các màn của app.
 */
enum class Screen(val route: String) {
    // Onboarding (sau IAP, rẽ theo first-open)
    Intro("intro"),
    GuidePermission("guide_permission"),
    Permission("permission"),

    // Hub
    Home("home"),

    // Quản lý app
    UserApp("user_app"),
    DetailUserApp("detail_user_app"),       // arg: packageName
    SystemApp("system_app"),
    ManagerApp("manager_app"),
    DetailManagerApp("detail_manager_app"), // arg: packageName

    // Quét & cập nhật
    ScanNow("scan_now"),
    UpdateAvailable("update_available"),

    // Bảo trì & thông tin
    RemoveApp("remove_app"),
    Uninstall("uninstall"),                 // feature uninstall (KHÁC Uninstall-survey của lib)
    InfoDevice("info_device"),
    History("history"),

    // Cài đặt
    Setting("setting"),
    LanguageSetting("language_setting"),
    TestAds("test_ads");

    companion object {
        const val ARG_PACKAGE = "packageName"
        fun detailUserApp(pkg: String) = "${DetailUserApp.route}/$pkg"
        fun detailManagerApp(pkg: String) = "${DetailManagerApp.route}/$pkg"
    }
}
