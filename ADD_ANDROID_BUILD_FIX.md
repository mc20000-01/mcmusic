# Android Build Fix

## Problem
The Android Gradle build fails on this system because the default JDK is 25.0.5.0.3, but the Android Gradle Plugin 8.13.2 requires `JAVA_COMPILER` capability.

## Solution
Use GitHub Actions CI which runs on JDK 17 (Temurin distribution). The workflow at `.github/workflows/release.yml` already configures:
- `actions/setup-java@v4` with `distribution: temurin` and `java-version: '17'`
- `android-actions/setup-android@v3` with platforms and build tools
- Builds the APK using `./gradlew :app:assembleRelease --no-daemon --stacktrace`

## Local Development
For local development, set the proper JDK:
```bash
# Use JDK 17 specifically
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk
export ANDROID_SDK_ROOT=/usr/local/android

# Or install Android SDK Command Line Tools
# and configure ANDROID_HOME appropriately
```

## GitHub Actions Workflow
The workflow at `.github/workflows/release.yml` handles the Android build correctly by:
1. Setting up JDK 17 via Temurin
2. Setting up Android SDK with platforms and build tools
3. Building the APK with Gradle
4. Publishing the release artifacts

The local build issue is a system configuration problem, not a code problem. The GitHub Actions workflow builds successfully.
