package com.supportsoftware.checkerpro.ui.screen.apps

import com.supportsoftware.checkerpro.ui.components.AppCard
import android.content.Intent
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.supportsoftware.checkerpro.R
import com.supportsoftware.checkerpro.advertisement.NativeAdSlot
import com.supportsoftware.checkerpro.ui.components.AppIcon
import com.supportsoftware.checkerpro.ui.components.AppScreen
import com.supportsoftware.checkerpro.ui.components.PillTabs

@Composable
fun DetailUserAppScreen(onBack: () -> Unit, vm: AppDetailViewModel = hiltViewModel()) {
    LaunchedEffect(Unit) { vm.checkVersion() }
    val state by vm.state.collectAsState()
    val context = LocalContext.current
    val app = state.app

    AppScreen(title = app?.appName ?: "App Detail", onBack = onBack) { m ->
        if (app == null) {
            Column(m.fillMaxSize(), verticalArrangement = Arrangement.Center, horizontalAlignment = Alignment.CenterHorizontally) {
                if (state.loading) CircularProgressIndicator() else Text("App not found")
            }
            return@AppScreen
        }
        Column(m.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                AppIcon(app.packageName, Modifier.size(64.dp))
                Column(Modifier.padding(start = 12.dp)) {
                    Text(app.appName, fontWeight = FontWeight.Bold, fontSize = 18.sp)
                    Text(app.packageName, fontSize = 12.sp, color = Color.Gray)
                    Text("Installed: v${app.versionName ?: "?"}", fontSize = 13.sp)
                }
            }
            NativeAdSlot("native_user_detail_app", Modifier.padding(vertical = 16.dp))

            when {
                state.versionChecking -> Row(verticalAlignment = Alignment.CenterVertically) {
                    CircularProgressIndicator(Modifier.size(18.dp)); Text("  Checking Play Store…")
                }
                state.version?.storeVersion != null -> {
                    val v = state.version!!
                    Text("Play Store version: ${v.storeVersion}", fontSize = 14.sp)
                    Text(
                        if (v.needsUpdate) stringResource(R.string.updateAvailable) else stringResource(R.string.updateNotAvailable),
                        color = if (v.needsUpdate) Color(0xFFD32F2F) else Color(0xFF2E7D32),
                        fontWeight = FontWeight.SemiBold,
                    )
                }
                else -> Text("Could not fetch store version", color = Color.Gray, fontSize = 13.sp)
            }

            Button(
                onClick = {
                    val url = state.version?.storeUrl
                        ?: "https://play.google.com/store/apps/details?id=${app.packageName}"
                    runCatching {
                        context.startActivity(
                            Intent(Intent.ACTION_VIEW, Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        )
                    }
                },
                modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
            ) {
                Text(if (state.version?.needsUpdate == true) stringResource(R.string.update_on_play) else stringResource(R.string.view_on_play))
            }
        }
    }
}

@Composable
fun DetailManagerAppScreen(onBack: () -> Unit, vm: AppDetailViewModel = hiltViewModel()) {
    LaunchedEffect(Unit) { vm.loadPermissions() }
    val state by vm.state.collectAsState()
    var tab by rememberSaveable { mutableIntStateOf(0) }
    var hasUsagePerm by remember { mutableStateOf(vm.hasUsageStats()) }
    val app = state.app

    // Xin quyền Usage Access ngay khi user vào tab "Usage" nếu chưa có (yêu cầu của user).
    val usageLauncher = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) {
        hasUsagePerm = vm.hasUsageStats()
        if (hasUsagePerm) vm.refreshUsage()
    }
    LaunchedEffect(tab) {
        if (tab == 1) {
            if (vm.hasUsageStats()) {
                hasUsagePerm = true
                vm.refreshUsage()
            } else {
                runCatching { usageLauncher.launch(vm.usageAccessIntent()) }
            }
        }
    }

    AppScreen(title = app?.appName ?: "App Detail", onBack = onBack) { m ->
        Column(m.fillMaxSize()) {
            // Card thông tin app (khớp RN header detail)
            if (app != null) {
                AppCard(Modifier.fillMaxWidth().padding(12.dp)) {
                    Column(Modifier.fillMaxWidth().padding(16.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                        AppIcon(app.packageName, Modifier.size(56.dp))
                        Text(app.appName, fontWeight = FontWeight.Bold, fontSize = 18.sp, color = Color(0xFF2196F3), modifier = Modifier.padding(top = 8.dp))
                        Text("Version: ${app.versionName ?: "?"}", fontSize = 13.sp)
                    }
                }
            }
            NativeAdSlot("native_app_detail_manager", Modifier.padding(horizontal = 8.dp))
            PillTabs(listOf(stringResource(R.string.permission), stringResource(R.string.app_usage)), tab, { tab = it })
            if (tab == 0) PermissionsTab(vm) else UsageTab(vm, hasUsagePerm) {
                runCatching { usageLauncher.launch(vm.usageAccessIntent()) }
            }
        }
    }
}

@Composable
private fun PermissionsTab(vm: AppDetailViewModel) {
    val state by vm.state.collectAsState()
    val perms = state.permissions
    if (perms == null) {
        CircularProgressIndicator(Modifier.padding(24.dp))
        return
    }
    LazyColumn(Modifier.fillMaxSize()) {
        if (perms.granted.isNotEmpty()) {
            item { SectionHeader("${stringResource(R.string.granted_label)} (${perms.granted.size})") }
            items(perms.granted) { PermissionRow(it, true) }
        }
        if (perms.denied.isNotEmpty()) {
            item { SectionHeader("${stringResource(R.string.not_granted_label)} (${perms.denied.size})") }
            items(perms.denied) { PermissionRow(it, false) }
        }
        if (perms.granted.isEmpty() && perms.denied.isEmpty()) {
            item { Text(stringResource(R.string.no_permissions), Modifier.padding(16.dp), color = Color.Gray) }
        }
    }
}

@Composable
private fun UsageTab(vm: AppDetailViewModel, hasPermission: Boolean, onGrant: () -> Unit) {
    val state by vm.state.collectAsState()
    val usage = state.usage
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        when {
            !hasPermission -> {
                Text(stringResource(R.string.no_usage_perm), color = Color.Gray)
                Button(onClick = onGrant, modifier = Modifier.padding(top = 12.dp)) { Text(stringResource(R.string.grantPermission)) }
            }
            usage == null -> AppCard(Modifier.fillMaxWidth()) {
                Row(Modifier.fillMaxWidth().padding(16.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(stringResource(R.string.today_usage), fontWeight = FontWeight.SemiBold)
                    Text("0m", color = Color(0xFF2196F3), fontWeight = FontWeight.SemiBold)
                }
            }
            else -> {
                AppCard(Modifier.fillMaxWidth()) {
                    Row(Modifier.fillMaxWidth().padding(16.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(stringResource(R.string.today_usage), fontWeight = FontWeight.SemiBold)
                        Text(formatDuration(usage.totalTimeInForeground), color = Color(0xFF2196F3), fontWeight = FontWeight.SemiBold)
                    }
                }
                Text("${stringResource(R.string.launches_today)}: ${usage.launchCount}", fontSize = 14.sp, color = Color.Gray, modifier = Modifier.padding(top = 12.dp))
            }
        }
    }
}

@Composable
private fun SectionHeader(text: String) {
    Text(text, fontWeight = FontWeight.Bold, modifier = Modifier.fillMaxWidth().padding(16.dp, 12.dp, 16.dp, 4.dp))
}

@Composable
private fun PermissionRow(permission: String, granted: Boolean) {
    Row(Modifier.fillMaxWidth().padding(16.dp, 6.dp), verticalAlignment = Alignment.CenterVertically) {
        Text(if (granted) "✓" else "✕", color = if (granted) Color(0xFF2E7D32) else Color(0xFFD32F2F))
        Text(permission.removePrefix("android.permission."), Modifier.padding(start = 8.dp), fontSize = 13.sp)
    }
    HorizontalDivider(thickness = 0.5.dp, color = Color(0x14000000))
}

private fun formatDuration(ms: Long): String {
    val totalSec = ms / 1000
    val h = totalSec / 3600
    val m = (totalSec % 3600) / 60
    val s = totalSec % 60
    return when {
        h > 0 -> "${h}h ${m}m"
        m > 0 -> "${m}m ${s}s"
        else -> "${s}s"
    }
}
