# Conservative release rules: keep the manifest/framework entry points and
# libraries that rely on reflection or runtime metadata, let R8 shrink the
# rest. CI compiles the release APK and will catch any missing rule.
-keepattributes *Annotation*, InnerClasses, EnclosingMethod, Signature, Exceptions, SourceFile, LineNumberTable

# Activities, services and receivers are instantiated by name from the manifest
# or AppWidgetManager, not from code that R8 can see.
-keep class dev.mcmusic.app.MainActivity { *; }
-keep class dev.mcmusic.app.playback.** { *; }
-keep class dev.mcmusic.app.widget.** { *; }

# Media3 discovers session/player implementations reflectively.
-keep class androidx.media3.** { *; }
-dontwarn androidx.media3.**

# Compose reads runtime metadata and keeps composable/group information alive
# through reflection; keep the runtime and Kotlin metadata intact. API models
# are built by hand from org.json, so there is no serializer to keep here.
-keep class androidx.compose.runtime.** { *; }
-keep class kotlin.Metadata { *; }
-dontwarn androidx.compose.**
-dontwarn kotlinx.coroutines.**
