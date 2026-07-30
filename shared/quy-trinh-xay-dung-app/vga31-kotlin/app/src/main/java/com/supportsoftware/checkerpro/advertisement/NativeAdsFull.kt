package com.supportsoftware.checkerpro.advertisement

import android.view.LayoutInflater
import android.view.View
import android.widget.Button
import android.widget.ImageView
import android.widget.TextView
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.zIndex
import com.supportsoftware.checkerpro.R
import com.google.android.gms.ads.nativead.MediaView
import com.google.android.gms.ads.nativead.NativeAd
import com.google.android.gms.ads.nativead.NativeAdView
import com.nlbn.ads.callback.NativeCallback
import com.nlbn.ads.util.Admob
import kotlinx.coroutines.delay

/**
 * Native ad "toàn màn" kiểu inter (port NativeAdsFull vga23b) — dùng cho MODAL Intro (positionIntrol NN).
 * Preload ngay khi vào cây; overlay đen full khi [start]=true; đếm ngược [countdownSec]s mới cho đóng.
 * Load lỗi / quá lâu → [onError] (caller đi tiếp). Dùng layout tự dựng [R.layout.ad_native_full].
 */
@Composable
fun NativeAdsFull(
    unitId: String,
    modifier: Modifier = Modifier,
    countdownSec: Int = 2,
    onClose: () -> Unit = {},
    onError: (() -> Unit)? = null,
    onLoaded: (() -> Unit)? = null,
    start: Boolean = true,
) {
    if (unitId.isBlank()) return

    var nativeAd by remember { mutableStateOf<NativeAd?>(null) }
    var errored by remember { mutableStateOf(false) }
    var counter by remember { mutableStateOf(countdownSec) }
    val context = LocalContext.current

    LaunchedEffect(unitId) {
        Admob.getInstance().loadNativeAd(
            context.applicationContext, unitId,
            object : NativeCallback() {
                override fun onNativeAdLoaded(ad: NativeAd?) {
                    if (ad != null) { nativeAd?.destroy(); nativeAd = ad; onLoaded?.invoke() }
                    else { errored = true }
                }

                override fun onAdFailedToLoad() { errored = true }
            },
        )
    }
    // An toàn: lỗi / quá 6s chưa có ad → báo caller đi tiếp (tránh kẹt màn trắng).
    LaunchedEffect(errored) { if (errored) { println("ADS ERR " + "NativeAdsFull $unitId error"); onError?.invoke() } }
    LaunchedEffect(start, unitId) { if (start) { delay(6000); if (nativeAd == null) onError?.invoke() } }
    LaunchedEffect(start) { if (start) { counter = countdownSec; while (counter > 0) { delay(1000); counter -= 1 } } }
    DisposableEffect(Unit) { onDispose { nativeAd?.destroy() } }

    if (!start) return
    val ad = nativeAd ?: return
    Box(modifier.fillMaxSize().background(Color.White).zIndex(1000f)) {
        key(ad) {
            AndroidView(
                modifier = Modifier.fillMaxSize(),
                factory = { ctx ->
                    LayoutInflater.from(ctx).inflate(R.layout.ad_native_full, null)
                        .also { bindFull(it as NativeAdView, ad) }
                },
            )
        }
        Box(
            modifier = Modifier.align(Alignment.TopEnd).statusBarsPadding()
                .padding(top = 12.dp, end = 16.dp).size(28.dp)
                .background(Color(0x22000000), CircleShape)
                .clickable(enabled = counter == 0) { onClose() },
            contentAlignment = Alignment.Center,
        ) {
            if (counter == 0) Icon(Icons.Default.Close, "Close", tint = Color(0xFF6B7280), modifier = Modifier.size(18.dp))
            else Text(counter.toString(), color = Color(0xFF6B7280), fontSize = 14.sp)
        }
    }
}

/** Bind NativeAd vào ad_native_full (NativeAdView API thủ công). */
internal fun bindFull(adView: NativeAdView, ad: NativeAd) {
    val media = adView.findViewById<MediaView>(R.id.ad_media); adView.mediaView = media
    val headline = adView.findViewById<TextView>(R.id.ad_headline); adView.headlineView = headline; headline.text = ad.headline
    val body = adView.findViewById<TextView>(R.id.ad_body); adView.bodyView = body
    body.text = ad.body; body.visibility = if (ad.body.isNullOrEmpty()) View.GONE else View.VISIBLE
    val advertiser = adView.findViewById<TextView>(R.id.ad_advertiser); adView.advertiserView = advertiser
    advertiser.text = ad.advertiser; advertiser.visibility = if (ad.advertiser.isNullOrEmpty()) View.GONE else View.VISIBLE
    val icon = adView.findViewById<ImageView>(R.id.ad_app_icon); adView.iconView = icon
    val d = ad.icon?.drawable
    if (d != null) { icon.setImageDrawable(d); icon.visibility = View.VISIBLE } else icon.visibility = View.GONE
    val cta = adView.findViewById<Button>(R.id.ad_call_to_action); adView.callToActionView = cta; cta.text = ad.callToAction.orEmpty()
    adView.setNativeAd(ad)
}
