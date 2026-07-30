package com.supportsoftware.checkerpro.ui.nav

import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.supportsoftware.checkerpro.core.AppStorage
import com.supportsoftware.checkerpro.ui.screen.apps.DetailManagerAppScreen
import com.supportsoftware.checkerpro.ui.screen.apps.DetailUserAppScreen
import com.supportsoftware.checkerpro.ui.screen.apps.ManagerAppScreen
import com.supportsoftware.checkerpro.ui.screen.apps.SystemAppScreen
import com.supportsoftware.checkerpro.ui.screen.apps.UserAppScreen
import com.supportsoftware.checkerpro.ui.screen.device.InfoDeviceScreen
import com.supportsoftware.checkerpro.ui.screen.history.HistoryScreen
import com.supportsoftware.checkerpro.ui.screen.home.HomeScreen
import com.supportsoftware.checkerpro.ui.screen.onboarding.IntroScreen
import com.supportsoftware.checkerpro.ui.screen.scan.ScanNowScreen
import com.supportsoftware.checkerpro.ui.screen.scan.UpdateAvailableScreen
import com.supportsoftware.checkerpro.ui.screen.settings.SettingScreen
import com.supportsoftware.checkerpro.ui.screen.testads.TestAdsScreen
import com.supportsoftware.checkerpro.ui.screen.uninstall.RemoveAppScreen
import com.supportsoftware.checkerpro.ui.screen.uninstall.UninstallScreen

@Composable
fun AppNavHost(
    startRoute: String,
    navController: NavHostController = rememberNavController(),
) {
    val context = LocalContext.current
    fun back() { navController.popBackStack() }
    fun toHome() {
        AppStorage.setOnboardingDone(context)
        navController.navigate(Screen.Home.route) {
            popUpTo(0) { inclusive = true }   // xóa toàn bộ onboarding khỏi back stack
        }
    }

    NavHost(navController = navController, startDestination = startRoute) {

        // ---------- Onboarding: chỉ Intro → Home (KHÔNG xin quyền usage trước Home;
        // quyền Usage Access chỉ hỏi khi vào chi tiết app → tab App usage). ----------
        composable(Screen.Intro.route) {
            IntroScreen(onFinish = { toHome() })
        }

        // ---------- Hub ----------
        composable(Screen.Home.route) {
            HomeScreen(
                onNavigate = { route -> navController.navigate(route) },
                onOpenSettings = { navController.navigate(Screen.Setting.route) },
            )
        }

        // ---------- Quản lý app ----------
        composable(Screen.UserApp.route) {
            UserAppScreen(onBack = ::back, onAppClick = { navController.navigate(Screen.detailUserApp(it)) })
        }
        composable(Screen.SystemApp.route) {
            SystemAppScreen(onBack = ::back)
        }
        composable(Screen.ManagerApp.route) {
            ManagerAppScreen(onBack = ::back, onAppClick = { navController.navigate(Screen.detailManagerApp(it)) })
        }
        composable(
            route = "${Screen.DetailUserApp.route}/{${Screen.ARG_PACKAGE}}",
            arguments = listOf(navArgument(Screen.ARG_PACKAGE) { type = NavType.StringType }),
        ) { DetailUserAppScreen(onBack = ::back) }
        composable(
            route = "${Screen.DetailManagerApp.route}/{${Screen.ARG_PACKAGE}}",
            arguments = listOf(navArgument(Screen.ARG_PACKAGE) { type = NavType.StringType }),
        ) { DetailManagerAppScreen(onBack = ::back) }

        // ---------- Quét & cập nhật ----------
        composable(Screen.ScanNow.route) {
            ScanNowScreen(
                onBack = ::back,
                onFinished = {
                    navController.navigate(Screen.UpdateAvailable.route) {
                        popUpTo(Screen.ScanNow.route) { inclusive = true }
                    }
                },
            )
        }
        composable(Screen.UpdateAvailable.route) { UpdateAvailableScreen(onBack = ::back) }

        // ---------- Bảo trì & thông tin ----------
        composable(Screen.RemoveApp.route) { RemoveAppScreen(onBack = ::back) }
        composable(Screen.Uninstall.route) { UninstallScreen(onBack = ::back) }
        composable(Screen.InfoDevice.route) { InfoDeviceScreen(onBack = ::back) }
        composable(Screen.History.route) { HistoryScreen(onBack = ::back) }

        // ---------- Cài đặt ----------
        composable(Screen.Setting.route) { SettingScreen(onBack = ::back) }
        composable(Screen.TestAds.route) { TestAdsScreen(onBack = ::back) }
    }
}
