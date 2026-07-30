package com.supportsoftware.checkerpro.ui.screen.history

import com.supportsoftware.checkerpro.ui.components.AppCard
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.supportsoftware.checkerpro.R
import com.supportsoftware.checkerpro.advertisement.NativeAdSlot
import com.supportsoftware.checkerpro.data.db.ScanHistory
import com.supportsoftware.checkerpro.data.db.ScanHistoryDao
import com.supportsoftware.checkerpro.ui.components.AppScreen
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import javax.inject.Inject

@HiltViewModel
class HistoryViewModel @Inject constructor(
    private val dao: ScanHistoryDao,
) : ViewModel() {
    val history: StateFlow<List<ScanHistory>> =
        dao.observeAll().stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun clearAll() = viewModelScope.launch { dao.deleteAll() }
}

private val fmt = SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault())

@Composable
fun HistoryScreen(onBack: () -> Unit, vm: HistoryViewModel = hiltViewModel()) {
    val items by vm.history.collectAsState()

    AppScreen(
        title = stringResource(R.string.history),
        onBack = onBack,
        actions = {
            if (items.isNotEmpty()) {
                Text(
                    stringResource(R.string.clearHistory),
                    color = Color.White,
                    modifier = Modifier
                        .clickable { vm.clearAll() }
                        .padding(end = 12.dp),
                )
            }
        },
    ) { m ->
        Box(m.fillMaxSize()) {
            if (items.isEmpty()) {
                Text(stringResource(R.string.no_history), Modifier.align(Alignment.Center), color = Color.Gray)
            } else {
                LazyColumn(Modifier.fillMaxSize().padding(12.dp)) {
                    item(key = "ad_native_history") { NativeAdSlot("native_history", Modifier.padding(bottom = 12.dp), isSmall = true) }
                    items(items, key = { it.id }) { h ->
                        AppCard(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                            Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                                Column(Modifier.weight(1f)) {
                                    Text(fmt.format(Date(h.date)), fontWeight = FontWeight.SemiBold)
                                    Text("${h.installedCount} ${stringResource(R.string.apps_scanned)}", fontSize = 12.sp, color = Color.Gray)
                                }
                                Text(
                                    "${h.updateCount} ${stringResource(R.string.updates_count)}",
                                    color = if (h.updateCount > 0) Color(0xFFD32F2F) else Color(0xFF2E7D32),
                                    fontWeight = FontWeight.SemiBold,
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}
