package com.supportsoftware.checkerpro.ui.screen.testads

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.supportsoftware.checkerpro.firebase.Remote
import com.supportsoftware.checkerpro.ui.components.AppScreen
import com.google.android.gms.ads.MobileAds

@Composable
fun TestAdsScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    val remote = Remote.instance

    val placements = listOf(
        "open_splash", "inter_splash", "native_language", "native_home", "inter_home",
        "native_scan_update", "native_update_available", "native_user_app", "native_history",
        "native_device_info", "inter_uninstall",
    )

    AppScreen(title = "Test Ads", onBack = onBack) { m ->
        Column(m.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp)) {
            Button(
                onClick = { runCatching { MobileAds.openAdInspector(context) {} } },
                modifier = Modifier.fillMaxWidth(),
            ) { Text("Open Ad Inspector") }

            Text("Ad units (from ads_config)", fontWeight = FontWeight.Bold, modifier = Modifier.padding(top = 16.dp, bottom = 8.dp))
            placements.forEach { p ->
                Text(
                    "$p = ${remote.adUnit(p).ifBlank { "(empty)" }}",
                    fontFamily = FontFamily.Monospace,
                    fontSize = 11.sp,
                    modifier = Modifier.padding(vertical = 2.dp),
                )
            }
        }
    }
}
