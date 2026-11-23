package dev.mcmusic.app.data

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

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

    val isAdmin: Boolean get() = me?.isAdmin == true

    /** The shell uses this to keep every screen behind the sign-in gate. */
    val signedIn: Boolean get() = me != null

    suspend fun refresh() {
        loaded = false
        gateError = null
        // No credential means there is nothing to verify: go straight to the
        // sign-in gate instead of asking /api/me and showing an empty shell.
        if (Prefs.token.isNullOrBlank()) {
            me = null
            loaded = true
            return
        }
        Api.me().fold(
            onSuccess = { me = it },
            onFailure = { failure ->
                me = null
                if (failure is ApiException && failure.code == 401) {
                    // A revoked token must not leave a phantom session or an
                    // endless retry loop; the password gate is the way back.
                    Prefs.saveToken(null)
                    Prefs.saveUsername(null)
                    Api.clearCookies()
                } else {
                    // Wi-Fi blips must not throw away a perfectly good token.
                    gateError = failure.message ?: "could not reach the server"
                }
            },
        )
        loaded = true
    }

    /** End the session everywhere in the app; the shell falls back to sign-in. */
    suspend fun signOut() {
        Api.logout()
        me = null
        loaded = true
    }

    /** Sign in and publish the verified account to the whole app at once. */
    suspend fun signIn(username: String, password: String): Result<Me> =
        Api.login(username, password).onSuccess {
            me = it
            loaded = true
        }

    /** Finish a Rotur sign-in after the browser hands a device token back. */
    suspend fun acceptRoturToken(token: String): Result<Me> =
        Api.adoptToken(token).onSuccess {
            me = it
            loaded = true
        }
}
