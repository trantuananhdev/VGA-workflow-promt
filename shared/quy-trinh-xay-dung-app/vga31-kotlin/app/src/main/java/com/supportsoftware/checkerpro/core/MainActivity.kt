package com.supportsoftware.checkerpro.core

import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.appcompat.app.AppCompatActivity
import com.supportsoftware.checkerpro.advertisement.NativeInterHost
import com.supportsoftware.checkerpro.firebase.Remote
import com.supportsoftware.checkerpro.ui.nav.AppNavHost
import com.supportsoftware.checkerpro.ui.nav.Screen
import com.supportsoftware.checkerpro.ui.theme.AppTheme
import dagger.hilt.android.AndroidEntryPoint

/**
 * Home Activity — lib mở qua getHomeActivity() sau luồng Splash→Inter→Language→IAP.
 * KHÔNG khai MAIN/LAUNCHER. AppCompatActivity = FragmentActivity (cần để mở IapActivity của lib).
 *
 * Quyết định start destination (port AppNavigation.js của RN):
 *  - Deep-link shortcut "uninstall" → mở thẳng màn Uninstall.
 *  - Còn lại → gate Intro theo số lần mở (goToHomeNumber) + nguồn cài (isAdsCampaign):
 *      • Ad campaign:  Intro khi goToHomeNumber < count_app_open.
 *      • Organic:      Intro khi count_app_open ≤ goToHomeNumber < count_app_open + organic_number_not_guide.
 *    (Language do lib quản; đây chỉ chi phối màn Intro của app.)
 */
@AndroidEntryPoint
class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Áp ngôn ngữ đã lưu (mirror vga_48 MainActivity) — để mọi màn app hiển thị đúng locale.
        AppStorage.language(this)?.let { LocaleHelper.updateLocale(this, it) }

        // Đăng ký shortcut "Uninstall" trên launcher (port app-shortcut).
        ShortcutHelper.addUninstallShortcut(this)

        val startRoute = resolveStartRoute()

        setContent {
            AppTheme {
                AppNavHost(startRoute = startRoute)
                // Overlay hiển thị native-interstitial (fallback sau inter) khi AdManager yêu cầu.
                NativeInterHost()
            }
        }
    }

    private fun resolveStartRoute(): String {
        val shortcutId = ShortcutHelper.consumeShortcutId(intent)
        if (shortcutId == ShortcutHelper.SHORTCUT_UNINSTALL) {
            // Mở qua shortcut → không tính là "vào Home", không tăng counter (giống RN: RootRoute không mount).
            return Screen.Uninstall.route
        }

        val remote = Remote.instance
        val n = AppStorage.goToHomeNumber(this)              // lần mở hiện tại (≥1)
        AppStorage.setGoToHomeNumber(this, n + 1)            // +1 cho lần sau (RN tăng khi RootRoute mount)

        val countAppOpen = remote.getInt("count_app_open").let { if (it <= 0) 3 else it }
        val organic = remote.getInt("organic_number_not_guide").let { if (it < 0) 0 else it }
        val isAdsCampaign = InstallReferrerHelper.isAdsCampaign(this)  // cache in-memory, không block

        // goToHomeStatus = true → vào thẳng Home; false → hiện Intro (port AppNavigation.js).
        val goToHomeStatus = if (isAdsCampaign) {
            n >= countAppOpen
        } else {
            n < organic || n >= countAppOpen + organic
        }

        return if (goToHomeStatus) Screen.Home.route else Screen.Intro.route
    }
}
