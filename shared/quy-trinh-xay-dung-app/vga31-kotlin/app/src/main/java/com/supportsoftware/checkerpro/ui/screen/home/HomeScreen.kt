package com.supportsoftware.checkerpro.ui.screen.home

import com.supportsoftware.checkerpro.ui.components.AppCard
import android.content.Intent
import androidx.annotation.DrawableRes
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.supportsoftware.checkerpro.R
import com.supportsoftware.checkerpro.advertisement.AdManager
import com.supportsoftware.checkerpro.advertisement.NativeAdSlot
import com.supportsoftware.checkerpro.core.IapOpener
import com.supportsoftware.checkerpro.ui.components.AppHeader
import com.supportsoftware.checkerpro.ui.components.CheckForAppUpdateWithDialog
import com.supportsoftware.checkerpro.ui.components.findActivity
import com.supportsoftware.checkerpro.ui.nav.Screen
import com.supportsoftware.checkerpro.ui.theme.Primary

private data class HomeTile(val label: String, @DrawableRes val iconRes: Int, val onClick: () -> Unit)

@Composable
fun HomeScreen(
    onNavigate: (String) -> Unit,
    onOpenSettings: () -> Unit,
) {
    val context = LocalContext.current
    val activity = context.findActivity()

    // Điều hướng kèm interstitial (port handleNavigate của RN: inter_home).
    fun go(route: String) {
        if (activity != null) AdManager.showInter(activity, "inter_home") { onNavigate(route) }
        else onNavigate(route)
    }

    val tiles = listOf(
        HomeTile(stringResource(R.string.userApp), R.drawable.ic_tile_user_app) { go(Screen.UserApp.route) },
        HomeTile(stringResource(R.string.managerApp), R.drawable.ic_tile_manager_app) { go(Screen.ManagerApp.route) },
        HomeTile(stringResource(R.string.systemApp), R.drawable.ic_tile_system_app) { go(Screen.SystemApp.route) },
        HomeTile(stringResource(R.string.updateSystem), R.drawable.ic_tile_system_update) {
            runCatching { context.startActivity(Intent("android.settings.SYSTEM_UPDATE_SETTINGS")) }
        },
        HomeTile(stringResource(R.string.removeApp), R.drawable.ic_tile_uninstall) { go(Screen.RemoveApp.route) },
        HomeTile(stringResource(R.string.infoDevice), R.drawable.ic_tile_device_info) { go(Screen.InfoDevice.route) },
        HomeTile(stringResource(R.string.history), R.drawable.ic_tile_history) { go(Screen.History.route) },
    )

    CheckForAppUpdateWithDialog()

    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)) {
        AppHeader(title = stringResource(R.string.app_name), centerTitle = false, titleColor = Primary) {
            // Vương miện → mở màn đăng ký gói (IAP) của lib
            Text(
                "👑",
                fontSize = 22.sp,
                modifier = Modifier.padding(end = 10.dp).clickable { IapOpener.open(context, "home") },
            )
            // Bánh răng → Settings
            Text(
                "⚙",
                fontSize = 24.sp,
                color = Color.Black,
                modifier = Modifier.padding(end = 10.dp).clickable { onOpenSettings() },
            )
        }

        Column(
            Modifier.fillMaxSize().padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            // Card quét (khớp RN "Chạm để quét và kiểm tra cập nhật ứng dụng" + nút Quét ngay)
            AppCard(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text(
                        stringResource(R.string.titleMenu1),
                        fontSize = 16.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = Primary,
                    )
                    Button(onClick = { go(Screen.ScanNow.route) }, modifier = Modifier.padding(top = 12.dp)) {
                        Text(stringResource(R.string.scanNow), fontWeight = FontWeight.SemiBold)
                    }
                }
            }

            // Khi chưa có ad, slot không chiếm chỗ → spacedBy(12) của Column vẫn giữ khoảng cách.
            NativeAdSlot("native_home")

            LazyVerticalGrid(
                columns = GridCells.Fixed(2),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                modifier = Modifier.fillMaxSize(),
            ) {
                items(tiles) { tile -> TileCard(tile) }
            }
        }
    }
}

@Composable
private fun TileCard(tile: HomeTile) {
    AppCard(
        modifier = Modifier.fillMaxWidth().aspectRatio(1.25f).clickable(onClick = tile.onClick),
        shape = RoundedCornerShape(14.dp),
    ) {
        Column(
            Modifier.fillMaxSize().padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            Image(
                painter = painterResource(tile.iconRes),
                contentDescription = tile.label,
                modifier = Modifier.size(48.dp),
            )
            Text(
                tile.label,
                fontWeight = FontWeight.SemiBold,
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(top = 10.dp),
            )
        }
    }
}
