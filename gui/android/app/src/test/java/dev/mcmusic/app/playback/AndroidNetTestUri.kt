package android.net

import android.os.Parcel

/**
 * Minimal Uri for JVM unit tests.
 *
 * android.net.Uri's constructor is package-private and Uri.parse() is a stub
 * in the mockable android.jar used by testDebugUnitTest. Declaring the helper
 * in android.net lets a fake DataSource return a real Uri whose toString() is
 * the URL we want to test, without Robolectric or Mockito.
 */
class TestUri(private val text: String) : Uri() {
    override fun buildUpon(): Uri.Builder = Uri.Builder()
    override fun getAuthority(): String? = null
    override fun getEncodedAuthority(): String? = null
    override fun getEncodedFragment(): String? = null
    override fun getEncodedPath(): String? = null
    override fun getEncodedQuery(): String? = null
    override fun getEncodedSchemeSpecificPart(): String? = null
    override fun getEncodedUserInfo(): String? = null
    override fun getFragment(): String? = null
    override fun getHost(): String? = null
    override fun getLastPathSegment(): String? = null
    override fun getPath(): String? = null
    override fun getPathSegments(): List<String> = emptyList()
    override fun getPort(): Int = -1
    override fun getQuery(): String? = null
    override fun getScheme(): String? = null
    override fun getSchemeSpecificPart(): String? = null
    override fun getUserInfo(): String? = null
    override fun isHierarchical(): Boolean = true
    override fun isRelative(): Boolean = false
    override fun describeContents(): Int = 0
    override fun writeToParcel(dest: Parcel, flags: Int) = Unit
    override fun toString(): String = text
}
