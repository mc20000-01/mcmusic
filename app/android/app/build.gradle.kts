plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "dev.mcmusic.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "dev.mcmusic.app"
        minSdk = 26
        targetSdk = 34
        versionCode = 32
        versionName = "2.7.1"
        // Host running the mcmusic server. Editable on the login screen.
        buildConfigField("String", "DEFAULT_SERVER", "\"https://mcmusic.sdisk.us\"")
    }

    // Every build is signed with the same committed key: this machine, CI, and
    // any future checkout. Signing with the machine-local debug key made each
    // release fail to install over the previous one ("conflicts with another
    // package"), because Android refuses an update signed by a new key.
    val projectKey = file("../keystore/mcmusic.p12")
    signingConfigs {
        create("mcmusic") {
            storeFile = projectKey
            storeType = "pkcs12"
            storePassword = "mcmusic"
            keyAlias = "mcmusic"
            keyPassword = "mcmusic"
        }
    }

    buildTypes {
        getByName("debug") {
            signingConfig = if (projectKey.exists()) signingConfigs.getByName("mcmusic") else null
        }
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            signingConfig = if (projectKey.exists()) signingConfigs.getByName("mcmusic") else null
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    // compileSdk 36 is what Kyant's backdrop renderer requires; it also lets the
    // glass read the layer behind it instead of only tinting it.
    kotlin {
        compilerOptions {
            jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
        }
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    packaging {
        resources.excludes += "/META-INF/{AL2.0,LGPL2.1}"
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2026.03.01")
    implementation(composeBom)

    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.activity:activity-compose:1.9.2")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.6")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.6")

    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.material3:material3")

    implementation("androidx.media3:media3-exoplayer:1.4.1")
    implementation("androidx.media3:media3-common:1.4.1")

    implementation("io.github.kyant0:backdrop:1.0.6")

    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")

    debugImplementation("androidx.compose.ui:ui-tooling")
}
