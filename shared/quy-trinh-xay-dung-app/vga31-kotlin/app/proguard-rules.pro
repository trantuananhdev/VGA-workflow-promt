# ===========================================
# GOOGLE PLAY BILLING
# ===========================================
-keep class com.android.billingclient.api.** { *; }
-keep class com.android.billingclient.** { *; }
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}

# =====================================================================
# Tích hợp base-application (ads/IAP/notification của thư viện)
# =====================================================================
# --- Thư viện (đã có consumer rules trong AAR, giữ thêm cho chắc) ---
-keep class com.nlbn.** { *; }
-keep class com.brian.** { *; }
-keep class com.google.android.gms.ads.nativead.** { *; }

# --- AdMob mediation (Meta/Facebook Audience Network) — nạp bằng reflection ---
-keep class com.google.ads.mediation.** { *; }
-keep class com.facebook.ads.** { *; }
-dontwarn com.facebook.ads.**
-dontwarn com.facebook.ads.internal.**

# --- Gson: giữ generic signature + TypeToken + field @SerializedName ---
-keepattributes Signature, InnerClasses, EnclosingMethod, *Annotation*
-keep,allowobfuscation,allowshrinking class * extends com.google.gson.reflect.TypeToken
-keepclassmembers,allowobfuscation class * {
    @com.google.gson.annotations.SerializedName <fields>;
}

# --- Model / data của app (Room entities + DTO Gson/Retrofit) ---
-keep class com.supportsoftware.checkerpro.data.** { *; }

# --- jsoup (Play Store version scrape) ---
-keep class org.jsoup.** { *; }
-dontwarn org.jsoup.**

# --- Retrofit (giữ generic signature — theo NOTES_vga48 §B.1; cần khi R8 + Retrofit/Gson) ---
-keepattributes Exceptions, RuntimeVisibleAnnotations, RuntimeVisibleParameterAnnotations, AnnotationDefault
-dontwarn retrofit2.**
-keep,allowobfuscation,allowshrinking class retrofit2.Response
-keep,allowobfuscation,allowshrinking class kotlin.coroutines.Continuation
-if interface * { @retrofit2.http.* <methods>; }
-keep,allowoptimization,allowobfuscation,allowshrinking interface <1>

# --- Crashlytics: giữ stack trace đọc được ---
-keepattributes SourceFile,LineNumberTable

# --- Cảnh báo lành tính ---
-dontwarn de.hdodenhof.circleimageview.**
