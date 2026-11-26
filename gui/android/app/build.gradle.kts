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
        minSdk = 34
        targetSdk = 34
        versionCode = 54
        versionName = "4.1.0"
        buildConfigField("String", "DEFAULT_SERVER", "\"https://mcmusic.sdisk.us\"")
    }

    // Same key as every previous release, so an update installs over an existing
    // copy instead of failing with "conflicts with another package".
    val projectKey = file("../../../keystore/mcmusic.p12")
    if (!projectKey.exists()) error("Missing keystore/mcmusic.p12 — refusing unsigned release")
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
            // Keep rules in proguard-rules.pro cover the manifest/AppWidget
            // entry points, Media3 and Compose reflection. CI builds this
            // configuration on every release, so it is validated there.
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            signingConfig = if (projectKey.exists()) signingConfigs.getByName("mcmusic") else null
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

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

    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui-tooling-preview")

    val media3 = "1.11.1"
    implementation("androidx.media3:media3-exoplayer:$media3")
    implementation("androidx.media3:media3-session:$media3")

    debugImplementation("androidx.compose.ui:ui-tooling")

    testImplementation("junit:junit:4.13.2")
}
