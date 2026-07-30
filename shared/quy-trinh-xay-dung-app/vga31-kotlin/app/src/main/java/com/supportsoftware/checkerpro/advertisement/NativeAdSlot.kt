package com.supportsoftware.checkerpro.advertisement

import android.content.Context
import android.content.ContextWrapper
import android.view.LayoutInflater
import androidx.activity.ComponentActivity
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.viewmodel.compose.LocalViewModelStoreOwner
import androidx.lifecycle.viewmodel.compose.viewModel
import com.supportsoftware.checkerpro.firebase.Remote
import com.brian.base_iap.utils.IAPUtils
import com.google.android.gms.ads.nativead.NativeAd
import com.google.android.gms.ads.nativead.NativeAdView
import com.nlbn.ads.callback.NativeCallback
import com.nlbn.ads.util.Admob

private const val MIN_AD_REQUEST_INTERVAL_MS = 1_000L

/** Tìm ComponentActivity qua chuỗi ContextWrapper (LocalContext.current thường là ContextThemeWrapper). */
private tailrec fun Context.findComponentActivity(): ComponentActivity? = when (this) {
    is ComponentActivity -> this
    is ContextWrapper -> baseContext.findComponentActivity()
    else -> null
}

/** [AdsViewModel] scope theo Activity → cache sống xuyên điều hướng. */
@Composable
private fun rememberAdsViewModel(): AdsViewModel {
    val owner = LocalContext.current.findComponentActivity()
        ?: checkNotNull(LocalViewModelStoreOwner.current) { "No ViewModelStoreOwner" }
    return viewModel(viewModelStoreOwner = owner)
}

/**
 * Slot native — layout LIB (ads_native_bot_2) + shimmer (ads_native_bot_loading_2).
 * Trạng thái (loading/loaded/nativeAd) nằm trong [AdsViewModel.Slot] scope Activity → KHÔNG nạp lại
 * mỗi lần vào lại composition (đổi tab/pop-back/list recycle); quá interval mới nạp ad mới.
 * Ẩn hoàn toàn khi premium / placement off / load fail.
 *
 * @param onResolved bắn 1 lần khi ad "xong" (loaded=true / fail hoặc disabled=false) — gate UI (vd nút Continue).
 */
@Composable
fun NativeAdSlot(
    placement: String,
    modifier: Modifier = Modifier,
    // true → native GỌN (no-media) cho màn list: display ads_native_bot_no_media_short_main
    //        + shimmer ads_native_loading_short_main (họ _main của lib).
    isSmall: Boolean = false,
    onResolved: ((loaded: Boolean) -> Unit)? = null,
) {
    val remote = Remote.instance
    val adUnit = remember(placement) { remote.adUnit(placement) }
    val enabled = !IAPUtils.isPremium() && remote.isAdEnabled(placement) && adUnit.isNotBlank()
    if (!enabled) {
        LaunchedEffect(placement) { onResolved?.invoke(false) }
        return
    }

    val vm = rememberAdsViewModel()
    val slot = remember(placement) { vm.slot(placement) }
    val isLoading by slot.isLoading.collectAsState()
    val isLoaded by slot.isLoaded.collectAsState()
    val cachedAd by slot.nativeAd.collectAsState()
    // Đã lỗi/no-fill trong phiên này → ẨN slot (không shimmer, không retry) tránh kẹt loading (port 23b).
    var suppressedAfterError by remember(placement) { mutableStateOf(false) }

    LaunchedEffect(placement) { slot.prepareForEntry(MIN_AD_REQUEST_INTERVAL_MS) }

    when {
        suppressedAfterError -> Unit                          // lỗi → không hiện gì (hết kẹt shimmer)
        isLoaded -> NativeAdView2(cachedAd, modifier, isSmall)
        isLoading -> Shimmer(modifier, isSmall)
        else -> NativeLoader(
            adUnit = adUnit,
            modifier = modifier,
            isSmall = isSmall,
            loadOnMount = slot.shouldLoadOnMount(),
            onStartLoad = {
                println("ADSLOT " + "load START $placement unit=$adUnit"); slot.onStartLoad()
            },
            onLoaded = { slot.onLoaded() },
            onLoadedNative = { slot.onLoadedNative(it) },
            onImpression = { slot.onImpression() },
            onResolved = { loaded ->
                if (loaded) {
                    println("ADSLOT " + "loaded $placement ad=true")
                } else {
                    println("ADSLOT ERR " + "failed $placement (no-fill/lỗi) → ẩn slot")
                    slot.onError()               // QUAN TRỌNG: tắt isLoading (nếu không shimmer kẹt mãi)
                    suppressedAfterError = true   // ẩn slot, không retry
                }
                onResolved?.invoke(loaded)
            },
        )
    }
}

/** Nạp native qua lib rồi render. KHÔNG destroy khi dispose — [AdsViewModel.Slot] sở hữu vòng đời. */
@Composable
private fun NativeLoader(
    adUnit: String,
    modifier: Modifier,
    isSmall: Boolean,
    loadOnMount: Boolean,
    onStartLoad: () -> Unit,
    onLoaded: () -> Unit,
    onLoadedNative: (NativeAd) -> Unit,
    onImpression: () -> Unit,
    onResolved: (Boolean) -> Unit,
) {
    var nativeAd by remember { mutableStateOf<NativeAd?>(null) }
    val context = LocalContext.current
    LaunchedEffect(loadOnMount) {
        if (!loadOnMount) return@LaunchedEffect
        onStartLoad()
        Admob.getInstance().loadNativeAd(
            context.applicationContext, adUnit,
            object : NativeCallback() {
                override fun onNativeAdLoaded(ad: NativeAd?) {
                    if (ad != null) { nativeAd = ad; onLoadedNative(ad); onLoaded(); onResolved(true) }
                    else onResolved(false)
                }

                override fun onAdFailedToLoad() { onResolved(false) }
                override fun onAdImpression() { onImpression() }
            },
        )
    }
    nativeAd?.let { NativeAdView2(it, modifier, isSmall) }
}

/** Bind 1 LẦN qua key(ad) — ad đổi mới tạo lại view; tránh warning "bind 2 lần" của Admob.
 *  isSmall → layout gọn no-media (ads_native_bot_no_media_short_main); else full (ads_native_bot_2). */
@Composable
private fun NativeAdView2(nativeAd: NativeAd?, modifier: Modifier = Modifier, isSmall: Boolean = false) {
    val ad = nativeAd ?: return
    val layoutRes = if (isSmall) com.brian.base_application.R.layout.ads_native_bot_no_media_short_main
                    else com.brian.base_application.R.layout.ads_native_bot_2
    key(ad) {
        AndroidView(
            modifier = modifier.fillMaxWidth(),
            factory = { ctx ->
                (LayoutInflater.from(ctx).inflate(layoutRes, null) as NativeAdView)
                    .also { Admob.getInstance().pushAdsToViewCustom(ad, it) }
            },
        )
    }
}

/** Shimmer: isSmall → ads_native_loading_short_main (gọn); else ads_native_bot_loading_2 (full). */
@Composable
private fun Shimmer(modifier: Modifier = Modifier, isSmall: Boolean = false) {
    val layoutRes = if (isSmall) com.brian.base_application.R.layout.ads_native_loading_short_main
                    else com.brian.base_application.R.layout.ads_native_bot_loading_2
    AndroidView(
        modifier = modifier.fillMaxWidth(),
        factory = { ctx -> LayoutInflater.from(ctx).inflate(layoutRes, null) },
    )
}
