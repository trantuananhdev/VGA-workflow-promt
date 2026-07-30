package com.supportsoftware.checkerpro.ui.screen.apps

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.hilt.navigation.compose.hiltViewModel
import com.supportsoftware.checkerpro.R
import com.supportsoftware.checkerpro.ui.components.AppScreen
import com.supportsoftware.checkerpro.ui.components.PillTabs

/** UserApp — card căn giữa + nút "Check update" → DetailUserApp (khớp RN). */
@Composable
fun UserAppScreen(onBack: () -> Unit, onAppClick: (String) -> Unit, vm: AppListViewModel = hiltViewModel()) {
    LaunchedEffect(Unit) { vm.loadUser() }
    val state by vm.user.collectAsState()
    AppScreen(title = stringResource(R.string.userApp), onBack = onBack) { m ->
        AppListContent(state, "native_user_app", m) { app ->
            AppCardCentered(app) { onAppClick(app.packageName) }
        }
    }
}

/** SystemApp — card căn giữa, không nút (khớp RN). */
@Composable
fun SystemAppScreen(onBack: () -> Unit, vm: AppListViewModel = hiltViewModel()) {
    LaunchedEffect(Unit) { vm.loadSystem() }
    val state by vm.system.collectAsState()
    AppScreen(title = stringResource(R.string.systemApp), onBack = onBack) { m ->
        AppListContent(state, "native_system_app", m) { app ->
            AppCardCentered(app)
        }
    }
}

/** Tab User | System (port ManagerApp TabView), dòng row+chevron → DetailManagerApp. */
@Composable
fun ManagerAppScreen(onBack: () -> Unit, onAppClick: (String) -> Unit, vm: AppListViewModel = hiltViewModel()) {
    LaunchedEffect(Unit) { vm.loadUser(); vm.loadSystem() }
    val userState by vm.user.collectAsState()
    val systemState by vm.system.collectAsState()
    var tab by rememberSaveable { mutableIntStateOf(0) }

    AppScreen(title = stringResource(R.string.managerApp), onBack = onBack) { m ->
        Column(m.fillMaxSize()) {
            PillTabs(listOf(stringResource(R.string.userApp), stringResource(R.string.systemApp)), tab, { tab = it })
            val state = if (tab == 0) userState else systemState
            AppListContent(state, "native_app_manager", Modifier) { app ->
                AppRow(app) { onAppClick(app.packageName) }
            }
        }
    }
}
