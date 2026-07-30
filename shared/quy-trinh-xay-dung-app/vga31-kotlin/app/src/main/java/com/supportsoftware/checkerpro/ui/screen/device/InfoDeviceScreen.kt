package com.supportsoftware.checkerpro.ui.screen.device

import com.supportsoftware.checkerpro.ui.components.AppCard
import android.app.ActivityManager
import android.content.Context
import android.os.Build
import android.os.Environment
import android.os.StatFs
import androidx.annotation.DrawableRes
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.supportsoftware.checkerpro.R
import com.supportsoftware.checkerpro.advertisement.NativeAdSlot
import com.supportsoftware.checkerpro.ui.components.AppScreen
import com.supportsoftware.checkerpro.ui.theme.Primary

@Composable
fun InfoDeviceScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    val info = remember { deviceInfo(context) }

    AppScreen(title = stringResource(R.string.infoDevice), onBack = onBack) { m ->
        Column(m.fillMaxWidth().verticalScroll(rememberScrollState()).padding(12.dp)) {
            // Card 1: tên máy
            AppCard(Modifier.fillMaxWidth()) {
                Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                    Image(painterResource(R.drawable.ic_app_placeholder), null, Modifier.size(48.dp))
                    Text(info.name, fontSize = 20.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(start = 16.dp))
                }
            }

            // Card 2: RAM / ROM / CPU + android version
            AppCard(Modifier.fillMaxWidth().padding(top = 12.dp)) {
                Column(Modifier.padding(16.dp)) {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
                        SpecIcon(R.drawable.ic_ram, "RAM", info.ram)
                        SpecIcon(R.drawable.ic_rom, "ROM", info.rom)
                        SpecIcon(R.drawable.ic_cpu, "CPU", info.cpu)
                    }
                    KeyValue(stringResource(R.string.androidVersion), info.android, topPad = 16)
                }
            }

            // Card 3: chi tiết
            AppCard(Modifier.fillMaxWidth().padding(top = 12.dp)) {
                Column(Modifier.padding(16.dp)) {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        LabeledValue(stringResource(R.string.brand), info.brand, Modifier.weight(1f))
                        LabeledValue(stringResource(R.string.model), info.model, Modifier.weight(1f))
                        LabeledValue(stringResource(R.string.hardware), info.hardware, Modifier.weight(1f))
                    }
                    KeyValue(stringResource(R.string.Manufacturer), info.manufacturer, topPad = 14)
                    KeyValue(stringResource(R.string.screenResolution), info.resolution, topPad = 14)
                }
            }

            NativeAdSlot("native_device_info", Modifier.padding(top = 12.dp))
        }
    }
}

@Composable
private fun SpecIcon(@DrawableRes icon: Int, label: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Image(painterResource(icon), label, Modifier.size(30.dp))
        Text(label, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(top = 8.dp))
        Text(value, color = Primary, fontSize = 14.sp)
    }
}

@Composable
private fun KeyValue(label: String, value: String, topPad: Int = 0) {
    Column(Modifier.padding(top = topPad.dp)) {
        Text(label, fontWeight = FontWeight.SemiBold)
        Text(value, color = Primary, fontSize = 14.sp)
    }
}

@Composable
private fun LabeledValue(label: String, value: String, modifier: Modifier = Modifier) {
    Column(modifier) {
        Text(label, fontWeight = FontWeight.SemiBold, fontSize = 13.sp, color = Color.Black)
        Text(value, color = Primary, fontSize = 13.sp)
    }
}

private data class DeviceSpecs(
    val name: String, val ram: String, val rom: String, val cpu: String, val android: String,
    val brand: String, val model: String, val hardware: String, val manufacturer: String, val resolution: String,
)

private fun deviceInfo(context: Context): DeviceSpecs {
    val mem = ActivityManager.MemoryInfo().also {
        (context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager).getMemoryInfo(it)
    }
    val stat = StatFs(Environment.getDataDirectory().path)
    val totalStorage = stat.blockCountLong * stat.blockSizeLong
    val dm = context.resources.displayMetrics
    return DeviceSpecs(
        name = "${Build.MANUFACTURER.replaceFirstChar { it.uppercase() }} ${Build.MODEL}",
        ram = gb(mem.totalMem),
        rom = gb(totalStorage),
        cpu = Build.SUPPORTED_ABIS.firstOrNull() ?: "-",
        android = Build.VERSION.RELEASE,
        brand = Build.BRAND,
        model = Build.MODEL,
        hardware = Build.HARDWARE,
        manufacturer = Build.MANUFACTURER,
        resolution = "${dm.widthPixels} x ${dm.heightPixels} pixels",
    )
}

private fun gb(bytes: Long): String {
    val g = bytes / (1024.0 * 1024.0 * 1024.0)
    return if (g >= 1) "${Math.round(g)} GB" else "${Math.round(bytes / (1024.0 * 1024.0))} MB"
}
