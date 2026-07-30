package com.supportsoftware.checkerpro.ui.screen.onboarding

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import com.supportsoftware.checkerpro.firebase.Remote
import com.brian.base_iap.utils.IAPUtils
import kotlinx.coroutines.delay
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import com.supportsoftware.checkerpro.R
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.supportsoftware.checkerpro.advertisement.AdPositions
import com.supportsoftware.checkerpro.advertisement.NativeAdSlot
import com.supportsoftware.checkerpro.advertisement.NativeAdsFull
import com.supportsoftware.checkerpro.ui.components.AppScreen
import com.supportsoftware.checkerpro.ui.theme.Primary
import kotlinx.coroutines.launch

private data class Slide(
    @androidx.annotation.StringRes val titleRes: Int,
    @androidx.annotation.StringRes val subtitleRes: Int,
    @androidx.annotation.DrawableRes val imageRes: Int,
    val adPlacement: String,
)

private val slides = listOf(
    Slide(R.string.intro1, R.string.intro1Sub, R.drawable.intro1, "native_intro1"),
    Slide(R.string.intro2, R.string.intro2Sub, R.drawable.intro2, "native_intro2"),
    Slide(R.string.intro3, R.string.intro3Sub, R.drawable.intro3, "native_intro3"),
    Slide(R.string.intro4, R.string.intro4Sub, R.drawable.intro4, "native_intro4"),
)

@Composable
fun IntroScreen(onFinish: () -> Unit) {
    val pager = rememberPagerState(pageCount = { slides.size })
    val scope = rememberCoroutineScope()
    val page = pager.currentPage
    val last = page == slides.lastIndex
    val slide = slides[page]
    val remote = Remote.instance

    // positionIntrol (A/B): chọn 1 biến thể cho phiên intro. N=native INLINE dưới slide N;
    // NN(11/22/33/44)=native MODAL toàn màn khi RỜI slide N (port RN vga31b).
    val positions = remember { AdPositions.selected() }
    fun adOn(p: Int) = !IAPUtils.isPremium() &&
        remote.isAdEnabled(slides[p].adPlacement) && remote.adUnit(slides[p].adPlacement).isNotBlank()
    fun inlineOn(p: Int) = adOn(p) && positions.contains(p + 1)
    fun modalOn(p: Int) = adOn(p) && positions.contains((p + 1) * 11)

    val hasInline = inlineOn(page)
    // "Sẵn sàng": không có inline-ad → sẵn ngay; có → chỉ sẵn khi ad load xong (hoặc timeout 5s).
    val ready = remember { mutableStateMapOf<Int, Boolean>() }
    val pageReady = !hasInline || ready[page] == true

    // Modal toàn màn: page đang hiện (-1 = không), và đã hiện chưa (mỗi trang tối đa 1 lần).
    var modalPage by remember { mutableStateOf(-1) }
    val modalShown = remember { mutableStateMapOf<Int, Boolean>() }

    LaunchedEffect(page, hasInline) {
        if (hasInline && ready[page] != true) { delay(5000); ready[page] = true }
    }

    fun advance() { if (last) onFinish() else scope.launch { pager.animateScrollToPage(page + 1) } }
    fun onContinue() {
        // Trang có modal NN & chưa hiện → bật modal (chưa chuyển trang); ngược lại chuyển trang.
        if (modalOn(page) && modalShown[page] != true) { modalShown[page] = true; modalPage = page }
        else advance()
    }

    Box(Modifier.fillMaxSize()) {
        Column(Modifier.fillMaxSize().padding(16.dp)) {
            // Không có nút "Bỏ qua" toàn bộ intro — RN gốc không có control này, chỉ dots + nút Next/Start.
            HorizontalPager(state = pager, modifier = Modifier.weight(1f)) { p ->
                val s = slides[p]
                // RN gốc dùng ảnh minh hoạ cỡ cố định 360x360 (không full-bleed) + title/subtitle riêng.
                Column(
                    Modifier.fillMaxSize().padding(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center,
                ) {
                    androidx.compose.foundation.Image(
                        painter = androidx.compose.ui.res.painterResource(s.imageRes),
                        contentDescription = null,
                        modifier = Modifier.size(220.dp),
                    )
                    Text(stringResource(s.titleRes), fontSize = 22.sp, fontWeight = FontWeight.Bold, textAlign = TextAlign.Center, modifier = Modifier.padding(top = 24.dp))
                    Text(stringResource(s.subtitleRes), textAlign = TextAlign.Center, color = Color.Gray, modifier = Modifier.padding(top = 12.dp))
                }
            }

            Row(Modifier.fillMaxWidth().padding(vertical = 12.dp), horizontalArrangement = Arrangement.Center) {
                slides.indices.forEach { i ->
                    Box(
                        Modifier.padding(4.dp).size(if (i == page) 10.dp else 8.dp).clip(CircleShape)
                            .background(if (i == page) Primary else Color(0x33000000))
                    )
                }
            }

            Button(
                onClick = { onContinue() },
                enabled = pageReady,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (pageReady) {
                    Text(
                        if (last) stringResource(R.string.start) else stringResource(R.string.continue_btn),
                        fontWeight = FontWeight.Bold,
                    )
                } else {
                    CircularProgressIndicator(modifier = Modifier.size(22.dp), strokeWidth = 2.dp, color = Primary)
                }
            }

            // Native INLINE dưới cùng — chỉ khi positionIntrol chứa N. Load xong → bật nút Continue.
            if (hasInline) {
                NativeAdSlot(slide.adPlacement, Modifier.padding(top = 8.dp), onResolved = { ready[page] = true })
            }
        }

        // Native MODAL toàn màn (NN) — hiện khi rời trang; đóng/lỗi → chuyển trang.
        if (modalPage >= 0) {
            NativeAdsFull(
                unitId = remote.adUnit(slides[modalPage].adPlacement),
                onClose = { modalPage = -1; advance() },
                onError = { modalPage = -1; advance() },
            )
        }
    }
}

@Composable
fun GuidePermissionScreen(onAccept: () -> Unit) {
    AppScreen(title = "Before we start") { m ->
        Column(m.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.Center) {
            Text("This app needs two permissions", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(16.dp))
            GuideItem("📦", "Query installed apps", "To list and manage the apps installed on your device.")
            GuideItem("📊", "Usage access", "To show how much time you spend in each app.")
            Spacer(Modifier.height(8.dp))
            Text(
                "By continuing you accept our Privacy Policy.",
                color = Color.Gray, fontSize = 12.sp,
            )
            Spacer(Modifier.height(24.dp))
            Button(onClick = onAccept, modifier = Modifier.fillMaxWidth()) { Text("Accept & Continue") }
        }
    }
}

@Composable
private fun GuideItem(emoji: String, title: String, desc: String) {
    Row(Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
        Text(emoji, fontSize = 26.sp)
        Column(Modifier.padding(start = 12.dp)) {
            Text(title, fontWeight = FontWeight.SemiBold)
            Text(desc, color = Color.Gray, fontSize = 13.sp)
        }
    }
}

@Composable
fun PermissionScreen(onDone: () -> Unit, vm: PermissionViewModel = hiltViewModel()) {
    val context = LocalContext.current
    var granted by remember { mutableStateOf(vm.hasUsageStats()) }
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) {
        granted = vm.hasUsageStats()
    }

    AppScreen(title = "Permission") { m ->
        Column(m.fillMaxSize().padding(24.dp)) {
            Text("Usage Access", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Text(
                "Grant Usage Access so the app can show per-app usage statistics.",
                color = Color.Gray, modifier = Modifier.padding(top = 8.dp),
            )
            Spacer(Modifier.height(16.dp))
            OutlinedButton(
                onClick = { runCatching { launcher.launch(vm.usageAccessIntent()) } },
                enabled = !granted,
                modifier = Modifier.fillMaxWidth(),
            ) { Text(if (granted) "✓ Granted" else "Grant Usage Access") }

            NativeAdSlot("native_permission", Modifier.padding(vertical = 16.dp))
            Spacer(Modifier.weight(1f))
            Button(onClick = onDone, modifier = Modifier.fillMaxWidth()) { Text("Continue") }
        }
    }
}
