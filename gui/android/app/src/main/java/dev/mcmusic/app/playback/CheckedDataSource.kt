package dev.mcmusic.app.playback

import androidx.media3.datasource.DataSource
import androidx.media3.datasource.DataSpec
import dev.mcmusic.app.data.CleartextPolicy

/**
 * Enforce the cleartext policy at connect time, not just when the MediaItem is
 * built. ExoPlayer owns the socket and may follow redirects, so checking only
 * the URL handed to it would leave a gap.
 */
class CheckedDataSource(private val delegate: DataSource) : DataSource by delegate {
    override fun open(dataSpec: DataSpec): Long {
        CleartextPolicy.requireAllowed(dataSpec.uri.toString())
        return delegate.open(dataSpec)
    }
}

/** Wrap a factory so every source it creates is policy-checked on open. */
fun checkedFactory(delegate: DataSource.Factory): DataSource.Factory =
    DataSource.Factory { CheckedDataSource(delegate.createDataSource()) }
