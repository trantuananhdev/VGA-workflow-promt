package com.supportsoftware.checkerpro.ui.screen.scan

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Text
import com.supportsoftware.checkerpro.ui.components.AppCard
import com.supportsoftware.checkerpro.ui.theme.BgLight
import com.supportsoftware.checkerpro.ui.theme.Secondary
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import com.supportsoftware.checkerpro.ui.components.AppSearchBar
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.ViewModel
import androidx.hilt.navigation.compose.hiltViewModel
import com.supportsoftware.checkerpro.R
import com.supportsoftware.checkerpro.advertisement.NativeAdSlot
import com.supportsoftware.checkerpro.data.model.VersionCheckResult
import com.supportsoftware.checkerpro.data.repo.ScanResultStore
import com.supportsoftware.checkerpro.ui.components.AppIcon
import com.supportsoftware.checkerpro.ui.components.AppScreen
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject

@Composable
fun ScanNowScreen(onBack: () -> Unit, onFinished: () -> Unit, vm: ScanViewModel = hiltViewModel()) {
    LaunchedEffect(Unit) { vm.startScan() }
    val state by vm.state.collectAsState()

    // UI khớp vga31b: Card trắng + vòng tròn % (THEME_SECOND) + 3 dòng trạng thái + nút seeUpdate.
    // KHÔNG auto-navigate; user bấm "seeUpdate" (chỉ bật khi quét xong & có bản cập nhật) — giống RN.
    AppScreen(title = stringResource(R.string.scanForUpdate), onBack = onBack) { m ->
        Column(
            m.fillMaxSize().padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            AppCard(Modifier.fillMaxWidth().padding(top = 12.dp)) {
                Column(
                    Modifier.fillMaxWidth().padding(vertical = 20.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Box(Modifier.size(160.dp), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator(
                            progress = { state.progress },
                            modifier = Modifier.fillMaxSize(),
                            color = Secondary,
                            trackColor = BgLight,
                            strokeWidth = 10.dp,
                        )
                        if (state.done) {
                            Text("✓", fontSize = 56.sp, color = Secondary, fontWeight = FontWeight.Bold)
                        } else {
                            Text(
                                "${(state.progress * 100).toInt()}%",
                                fontSize = 20.sp, fontWeight = FontWeight.Medium, color = Color(0xFF0C0C0C),
                            )
                        }
                    }

                    Column(Modifier.fillMaxWidth().padding(horizontal = 32.dp, vertical = 8.dp)) {
                        StatusRow(
                            stringResource(if (state.done) R.string.scanned else R.string.scanning),
                            if (state.done) "✓" else "...",
                        )
                        StatusRow(stringResource(R.string.installedApp), if (state.done) "${state.total}" else "...")
                        StatusRow(stringResource(R.string.updateAvailable), if (state.done) "${state.updates.size}" else "...")
                    }

                    Button(
                        onClick = { if (state.updates.isNotEmpty()) onFinished() },
                        enabled = state.done && state.updates.isNotEmpty(),
                        modifier = Modifier.fillMaxWidth().padding(horizontal = 24.dp, vertical = 12.dp),
                    ) { Text(stringResource(R.string.seeUpdate)) }
                }
            }

            NativeAdSlot("native_scan_update", Modifier.padding(top = 16.dp))
        }
    }
}

@Composable
private fun StatusRow(label: String, value: String) {
    Row(
        Modifier.fillMaxWidth().padding(vertical = 6.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(label, fontSize = 14.sp, fontWeight = FontWeight.Medium)
        Text(value, fontSize = 14.sp, fontWeight = FontWeight.Medium, color = Color.Gray)
    }
}

@HiltViewModel
class UpdateAvailableViewModel @Inject constructor(
    private val store: ScanResultStore,
) : ViewModel() {
    val updates: List<VersionCheckResult> get() = store.lastUpdates
}

@Composable
fun UpdateAvailableScreen(onBack: () -> Unit, vm: UpdateAvailableViewModel = hiltViewModel()) {
    val context = LocalContext.current
    val updates = vm.updates
    var query by rememberSaveable { mutableStateOf("") }
    val filtered = remember(updates, query) {
        if (query.isBlank()) updates
        else updates.filter { it.packageName.contains(query, ignoreCase = true) }
    }

    AppScreen(title = stringResource(R.string.updateAvailable), onBack = onBack) { m ->
        if (updates.isEmpty()) {
            Column(m.fillMaxSize(), verticalArrangement = Arrangement.Center, horizontalAlignment = Alignment.CenterHorizontally) {
                Text("🎉", fontSize = 48.sp)
                Text(stringResource(R.string.up_to_date_all), color = Color.Gray, modifier = Modifier.padding(top = 8.dp))
            }
            return@AppScreen
        }
        Column(m.fillMaxSize()) {
            AppSearchBar(query = query, onQueryChange = { query = it })
            LazyColumn(Modifier.fillMaxSize()) {
                item(key = "ad_native_update_available") { NativeAdSlot("native_update_available", Modifier.padding(8.dp), isSmall = true) }
                items(filtered, key = { it.packageName }) { u ->
                Row(
                    Modifier.fillMaxWidth().padding(16.dp, 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    AppIcon(u.packageName, Modifier.size(44.dp))
                    Column(Modifier.weight(1f).padding(start = 12.dp)) {
                        Text(u.packageName, fontWeight = FontWeight.SemiBold, maxLines = 1)
                        Text("${u.currentVersion ?: "?"} → ${u.storeVersion ?: "?"}", fontSize = 12.sp, color = Color.Gray)
                    }
                    Button(onClick = {
                        runCatching {
                            context.startActivity(
                                Intent(Intent.ACTION_VIEW, Uri.parse(u.storeUrl)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                            )
                        }
                    }) { Text(stringResource(R.string.update)) }
                }
                HorizontalDivider(thickness = 0.5.dp, color = Color(0x14000000))
                }
            }
        }
    }
}
