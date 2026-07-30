package com.supportsoftware.checkerpro.ui.screen.apps

import com.supportsoftware.checkerpro.ui.components.AppCard
import androidx.compose.foundation.clickable
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
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.supportsoftware.checkerpro.R
import com.supportsoftware.checkerpro.advertisement.NativeAdSlot
import com.supportsoftware.checkerpro.data.model.AppInfo
import com.supportsoftware.checkerpro.ui.components.AppIcon
import com.supportsoftware.checkerpro.ui.components.AppSearchBar
import com.supportsoftware.checkerpro.ui.theme.Primary
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private val dateFmt = SimpleDateFormat("MM/dd/yyyy", Locale.getDefault())

/** Row + chevron (dùng cho ManagerApp — khớp RN Quản lý ứng dụng). */
@Composable
fun AppRow(app: AppInfo, onClick: () -> Unit) {
    AppCard(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 6.dp).clickable(onClick = onClick),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            AppIcon(app.packageName, Modifier.size(48.dp))
            Column(Modifier.weight(1f).padding(start = 12.dp)) {
                Text(app.appName, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text(app.versionName ?: "?", fontSize = 13.sp, color = Color.Gray, maxLines = 1)
            }
            Text("›", fontSize = 26.sp, color = Primary)
        }
    }
}

/** Card căn giữa (dùng cho UserApp/SystemApp — khớp RN). [onCheck] != null → hiện nút "Kiểm tra cập nhật". */
@Composable
fun AppCardCentered(app: AppInfo, onCheck: (() -> Unit)? = null) {
    AppCard(modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 8.dp)) {
        Column(
            Modifier.fillMaxWidth().padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            AppIcon(app.packageName, Modifier.size(64.dp))
            Text(
                app.appName,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
                color = Primary,
                textAlign = TextAlign.Center,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.padding(top = 10.dp),
            )
            Text("${stringResource(R.string.lastUpdate)}: ${dateFmt.format(Date(app.lastUpdateTime))}", fontSize = 13.sp, modifier = Modifier.padding(top = 6.dp))
            Text("${stringResource(R.string.version)}: ${app.versionName ?: "?"}", fontSize = 13.sp, modifier = Modifier.padding(top = 2.dp))
            if (onCheck != null) {
                Button(onClick = onCheck, modifier = Modifier.padding(top = 12.dp)) {
                    Text(stringResource(R.string.checkUpdate))
                }
            }
        }
    }
}

/**
 * List app + search (lọc theo tên + package) + native ad; [item] tùy màn quyết định layout dòng.
 */
@Composable
fun AppListContent(
    state: AppListState,
    nativePlacement: String,
    modifier: Modifier = Modifier,
    itemContent: @Composable (AppInfo) -> Unit,
) {
    var query by rememberSaveable { mutableStateOf("") }
    val filtered = remember(state.apps, query) {
        if (query.isBlank()) state.apps
        else state.apps.filter {
            it.appName.contains(query, ignoreCase = true) ||
                it.packageName.contains(query, ignoreCase = true)
        }
    }

    Column(modifier.fillMaxSize()) {
        if (!state.loading && state.apps.isNotEmpty()) {
            AppSearchBar(query = query, onQueryChange = { query = it })
        }
        Box(Modifier.fillMaxSize()) {
            when {
                state.loading -> CircularProgressIndicator(Modifier.align(Alignment.Center))
                state.apps.isEmpty() -> Text(stringResource(R.string.no_apps_found), Modifier.align(Alignment.Center), color = Color.Gray)
                filtered.isEmpty() -> Text("${stringResource(R.string.search_hint)}", Modifier.align(Alignment.Center), color = Color.Gray)
                else -> LazyColumn(verticalArrangement = Arrangement.Top) {
                    item(key = "ad_$nativePlacement") { NativeAdSlot(nativePlacement, Modifier.padding(8.dp), isSmall = true) }
                    items(filtered, key = { it.packageName }) { app -> itemContent(app) }
                }
            }
        }
    }
}
