package dev.mcmusic.app.playback

import androidx.media3.datasource.DataSource
import androidx.media3.datasource.DataSpec
import dev.mcmusic.app.data.CleartextPolicy
import java.io.IOException

/**
 * Enforce the cleartext policy at connect time, not just when the MediaItem is
 * built. ExoPlayer owns the socket and may follow redirects, so checking only
 * the URL handed to it would leave a gap.
 */
class CheckedDataSource(private val delegate: DataSource) : DataSource by delegate {
    override fun open(dataSpec: DataSpec): Long {
        CleartextPolicy.requireAllowed(dataSpec.uri.toString())
        val length = delegate.open(dataSpec)
        try {
            // DefaultHttpDataSource follows redirects inside open(); getUri()
            // is the final URI after those redirects. Recheck it so an allowed
            // local URL cannot be redirected to a public cleartext host.
            CleartextPolicy.requireAllowed(delegate.uri.toString())
        } catch (error: SecurityException) {
            try {
                delegate.close()
            } catch (_: IOException) {
                // Keep the policy failure as the cause worth reporting.
            }
            throw error
        }
        return length
    }
}

/** Wrap a factory so every source it creates is policy-checked on open. */
fun checkedFactory(delegate: DataSource.Factory): DataSource.Factory =
    DataSource.Factory { CheckedDataSource(delegate.createDataSource()) }
