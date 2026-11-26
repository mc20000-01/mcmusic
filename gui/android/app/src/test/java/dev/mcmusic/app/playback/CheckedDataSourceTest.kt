package dev.mcmusic.app.playback

import android.net.TestUri
import android.net.Uri
import androidx.media3.datasource.DataSource
import androidx.media3.datasource.DataSpec
import androidx.media3.datasource.TransferListener
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Test

/** JVM coverage for the check after DefaultHttpDataSource follows redirects. */
class CheckedDataSourceTest {
    private class FakeDataSource(private val finalUri: Uri) : DataSource {
        var current: Uri = TestUri("about:blank")
        var closed = false

        override fun addTransferListener(transferListener: TransferListener) = Unit

        override fun open(dataSpec: DataSpec): Long {
            // Mimic DefaultHttpDataSource: the URI exposed after open() is the
            // final one, which may differ from dataSpec.uri.
            current = finalUri
            return 7L
        }

        override fun getUri(): Uri = current
        override fun close() {
            closed = true
        }
        override fun read(buffer: ByteArray, offset: Int, length: Int): Int = -1
    }

    @Test
    fun rejectsRedirectToPublicCleartextHostAndClosesDelegate() {
        val delegate = FakeDataSource(TestUri("http://8.8.8.8/x"))
        val source = CheckedDataSource(delegate)
        val spec = DataSpec.Builder()
            .setUri(TestUri("http://192.168.1.5:8000/api/tracks"))
            .build()

        try {
            source.open(spec)
            fail("a redirect to a public HTTP host was accepted")
        } catch (_: SecurityException) {
            // expected
        }
        assertTrue("the rejected source must be closed", delegate.closed)
    }

    @Test
    fun allowsRedirectInsidePrivateRangeAndKeepsDelegateOpen() {
        val delegate = FakeDataSource(TestUri("http://10.0.0.9/x"))
        val source = CheckedDataSource(delegate)
        val spec = DataSpec.Builder()
            .setUri(TestUri("http://192.168.1.5:8000/api/tracks"))
            .build()

        assertEquals(7L, source.open(spec))
        assertEquals("http://10.0.0.9/x", delegate.current.toString())
        assertFalse(delegate.closed)
    }
}
