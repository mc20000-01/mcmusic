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

    val isAdmin: Boolean get() = me?.isAdmin == true

    suspend fun refresh() {
        me = Api.me()
        loaded = true
    }

    /** Sign in and publish the verified account to the whole app at once. */
    suspend fun signIn(username: String, password: String): Result<Me> =
        Api.login(username, password).onSuccess {
            me = it
            loaded = true
        }
}
