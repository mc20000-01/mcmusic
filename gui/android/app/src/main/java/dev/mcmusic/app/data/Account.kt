package dev.mcmusic.app.data

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

/**
 * The signed-in account, shared by the shell and the screens. The admin tab and
 * the admin screen read this instead of each fetching `/api/me` on their own, so
 * signing in (or losing admin rights) updates the whole app at once.
 */
object Account {
    var me by mutableStateOf<Me?>(null)
        private set

    var loaded by mutableStateOf(false)
        private set

    /** Why a stored token could not be verified, shown on the sign-in gate. */
    var gateError by mutableStateOf<String?>(null)
        private set

    /** Non-blocking clue for a saved session that could not be revalidated. */
    var status by mutableStateOf<String?>(null)
        private set

    val isAdmin: Boolean get() = me?.isAdmin == true

    /** The shell uses this to keep every screen behind the sign-in gate. */
    val signedIn: Boolean get() = me != null

    /** Serializes cold-start refresh, onResume refresh and deep-link adoption. */
    private val sessionLock = Mutex()

    /** Show the last verified identity immediately; verification happens in the background. */
    fun restoreCached() {
        if (loaded) return
        val hasCredential = !Prefs.token.isNullOrBlank() || !Prefs.pendingToken.isNullOrBlank()
        me = if (hasCredential) Prefs.cachedMe() else null
        status = null
        gateError = null
        loaded = true
    }

    suspend fun refresh() = sessionLock.withLock {
        gateError = null
        if (Prefs.token.isNullOrBlank() && Prefs.pendingToken.isNullOrBlank()) {
            me = null
            status = null
            loaded = true
            return@withLock
        }

        // A deep-link token may have arrived while the server was unreachable.
        // Adopt it before /api/me so a transient failure cannot strand the user
        // on the gate with a token that was never persisted.
        val pending = Prefs.pendingToken
        if (!pending.isNullOrBlank()) {
            Api.verifyToken(pending).fold(
                onSuccess = { verified ->
                    Prefs.saveToken(pending)
                    completeSignIn(verified)
                    Prefs.savePendingToken(null)
                    status = null
                },
                onFailure = { failure ->
                    if (failure is ApiException && failure.code == 401) {
                        clearSession()
                        me = null
                        gateError = failure.message
                        status = null
                    } else {
                        // Keep the cached identity and the pending token for the
                        // next onResume; this is a network problem, not a logout.
                        status = "Could not verify Rotur sign-in — will retry"
                    }
                },
            )
            loaded = true
            if (me == null && !signedIn) return@withLock
        }

        val token = Prefs.token ?: run {
            loaded = true
            return@withLock
        }
        if (token.isBlank()) {
            loaded = true
            return@withLock
        }
        Api.me().fold(
            onSuccess = { verified ->
                me = verified
                Prefs.saveCachedMe(verified)
                status = null
            },
            onFailure = { failure ->
                if (failure is ApiException && failure.code == 401) {
                    // A revoked token must not leave a phantom session or an
                    // endless retry loop; the password gate is the way back.
                    clearSession()
                    me = null
                    gateError = failure.message
                    status = null
                } else {
                    // Wi-Fi blips must not throw away a perfectly good token or
                    // the cached identity that keeps the app usable offline.
                    status = "Offline — using your saved session"
                }
            },
        )
        loaded = true
    }

    /** End the session everywhere in the app; the shell falls back to sign-in. */
    suspend fun signOut() {
        Api.logout()
        clearSession()
        me = null
        status = null
        gateError = null
        loaded = true
    }

    /** Sign in and publish the verified account to the whole app at once. */
    suspend fun signIn(username: String, password: String): Result<Me> =
        Api.login(username, password).onSuccess { completeSignIn(it) }

    /**
     * Finish a Rotur sign-in after the browser hands a device token back. The
     * token is persisted before the request, so a Wi-Fi blip cannot lose it.
     */
    suspend fun acceptRoturToken(token: String): Result<Me> = sessionLock.withLock {
        if (token.isBlank()) return@withLock Result.failure(IllegalArgumentException("empty token"))
        Prefs.savePendingToken(token)
        val result = Api.verifyToken(token)
        result.fold(
            onSuccess = {
                Prefs.saveToken(token)
                completeSignIn(it)
                Prefs.savePendingToken(null)
                status = null
                gateError = null
                loaded = true
            },
            onFailure = { failure ->
                if (failure is ApiException && failure.code == 401) {
                    clearSession()
                    me = null
                    gateError = failure.message
                    status = null
                } else {
                    // Keep the cached identity and the pending token; onResume
                    // adopts it once the server is reachable again.
                    status = "Rotur sign-in will retry when you are back online"
                }
                loaded = true
            },
        )
        result
    }

    private fun completeSignIn(verified: Me) {
        Prefs.saveUsername(verified.username)
        Prefs.saveCachedMe(verified)
        me = verified
        loaded = true
    }

    private fun clearSession() {
        Prefs.saveToken(null)
        Prefs.savePendingToken(null)
        Prefs.saveUsername(null)
        Prefs.saveCachedMe(null)
        Api.clearCookies()
    }
}
