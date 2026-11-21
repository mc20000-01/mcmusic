# Keep the media session bridge and Compose entry points intact if minification
# is ever enabled. Release builds currently leave minification off so stack
# traces stay readable, but the rules below make that a safe choice to change.
-keep class dev.mcmusic.app.playback.** { *; }
-keep class dev.mcmusic.app.widget.** { *; }
-keep class androidx.media3.** { *; }
-dontwarn androidx.media3.**
