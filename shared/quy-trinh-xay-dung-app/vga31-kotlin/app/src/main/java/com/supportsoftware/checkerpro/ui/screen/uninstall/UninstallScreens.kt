package com.supportsoftware.checkerpro.ui.screen.uninstall

import com.supportsoftware.checkerpro.ui.components.AppCard
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.supportsoftware.checkerpro.R
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.supportsoftware.checkerpro.advertisement.AdManager
import com.supportsoftware.checkerpro.advertisement.NativeAdSlot
import com.supportsoftware.checkerpro.data.model.AppInfo
import com.supportsoftware.checkerpro.data.repo.AppInventoryRepository
import com.supportsoftware.checkerpro.ui.components.AppIcon
import com.supportsoftware.checkerpro.ui.components.AppScreen
import com.supportsoftware.checkerpro.ui.components.AppSearchBar
import com.supportsoftware.checkerpro.ui.components.findActivity
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class UninstallViewModel @Inject constructor(
    private val repo: AppInventoryRepository,
) : ViewModel() {

    private val _apps = MutableStateFlow<List<AppInfo>?>(null)  // null = loading
    val apps: StateFlow<List<AppInfo>?> = _apps.asStateFlow()

    fun load() {
        if (_apps.value != null) return
        viewModelScope.launch { _apps.value = repo.getInstalledApps(systemApps = false) }
    }

    fun uninstallIntent(pkg: String) = repo.buildUninstallIntent(pkg)

    /** Sau khi quay lại từ dialog gỡ: nếu package đã biến mất thì bỏ khỏi danh sách. */
    fun onUninstallResult(pkg: String) {
        if (!repo.packageExists(pkg)) {
            _apps.value = _apps.value?.filterNot { it.packageName == pkg }
        }
    }
}

@Composable
private fun UninstallList(
    title: String,
    nativePlacement: String,
    onBack: () -> Unit,
    vm: UninstallViewModel,
) {
    LaunchedEffect(Unit) { vm.load() }
    val apps by vm.apps.collectAsState()
    var pending by remember { mutableStateOf<String?>(null) }
    var query by rememberSaveable { mutableStateOf("") }
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) {
        pending?.let { vm.onUninstallResult(it) }
        pending = null
    }
    val filtered = remember(apps, query) {
        val list = apps ?: return@remember null
        if (query.isBlank()) list
        else list.filter {
            it.appName.contains(query, ignoreCase = true) || it.packageName.contains(query, ignoreCase = true)
        }
    }

    AppScreen(title = title, onBack = onBack) { m ->
        Column(m.fillMaxSize()) {
            if (apps != null) AppSearchBar(query = query, onQueryChange = { query = it })
            Box(Modifier.fillMaxSize()) {
            when (val list = filtered) {
                null -> CircularProgressIndicator(Modifier.align(Alignment.Center))
                else -> LazyColumn(Modifier.fillMaxSize()) {
                    item(key = "ad_$nativePlacement") { NativeAdSlot(nativePlacement, Modifier.padding(8.dp), isSmall = true) }
                    items(list, key = { it.packageName }) { app ->
                        AppCard(Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 6.dp)) {
                            Row(
                                Modifier.fillMaxWidth().padding(12.dp),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                AppIcon(app.packageName, Modifier.size(46.dp))
                                Column(Modifier.weight(1f).padding(start = 12.dp)) {
                                    Text(app.appName, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                                    Text(uninstallDateFmt.format(Date(app.lastUpdateTime)), fontSize = 12.sp, color = Color.Gray)
                                }
                                // Nút thùng rác đỏ (khớp RN)
                                Box(
                                    Modifier
                                        .size(44.dp)
                                        .border(1.dp, Color(0xFFE53935), RoundedCornerShape(10.dp))
                                        .clickable {
                                            pending = app.packageName
                                            runCatching { launcher.launch(vm.uninstallIntent(app.packageName)) }
                                        },
                                    contentAlignment = Alignment.Center,
                                ) {
                                    Icon(
                                        painter = painterResource(R.drawable.ic_delete),
                                        contentDescription = "Uninstall ${app.appName}",
                                        tint = Color(0xFFE53935),
                                        modifier = Modifier.size(22.dp),
                                    )
                                }
                            }
                        }
                    }
                }
            }
            }
        }
    }
}

@Composable
fun RemoveAppScreen(onBack: () -> Unit, vm: UninstallViewModel = hiltViewModel()) {
    UninstallList(stringResource(R.string.removeApp), "native_uninstall_app", onBack, vm)
}

/** Màn Uninstall (feature) — KHÁC Uninstall-survey của lib. Hiện inter_uninstall khi mở. */
@Composable
fun UninstallScreen(onBack: () -> Unit, vm: UninstallViewModel = hiltViewModel()) {
    val activity = LocalContext.current.findActivity()
    LaunchedEffect(Unit) {
        if (activity != null) AdManager.showInter(activity, "inter_uninstall") {}
    }
    UninstallList(stringResource(R.string.uninstall), "native_uninstall_app", onBack, vm)
}

private val uninstallDateFmt = SimpleDateFormat("MM/dd/yyyy", Locale.getDefault())
