package dev.mcmusic.app.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.mcmusic.app.data.Api
import dev.mcmusic.app.data.Listener
import dev.mcmusic.app.ui.EmptyState
import dev.mcmusic.app.ui.McIcon
import dev.mcmusic.app.ui.ScreenTitle
import dev.mcmusic.app.ui.SectionLabel
import dev.mcmusic.app.ui.design.LocalDesign
import kotlinx.coroutines.launch

@Composable
fun SearchScreen() {
    val design = LocalDesign.current
    val scope = rememberCoroutineScope()
    var query by rememberSaveable { mutableStateOf("") }
    var directory by remember { mutableStateOf<List<Listener>>(emptyList()) }
    var profile by remember { mutableStateOf<Listener?>(null) }
    var message by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        directory = Api.listening().getOrDefault(emptyList())
    }

    fun lookUp() {
        val name = query.trim()
        if (name.isEmpty() || busy) return
        scope.launch {
            busy = true
            message = null
            Api.now(name).fold(
                onSuccess = { found ->
                    profile = found
                    if (found == null) message = "\"$name\" is not on this server"
                },
                onFailure = { message = it.message ?: "could not reach the server" },
            )
            busy = false
        }
    }

    val needle = query.trim().lowercase()
    val matches = if (needle.isEmpty()) emptyList() else directory.filter { listener ->
        listener.username.lowercase().contains(needle) ||
            listener.track?.title?.lowercase()?.contains(needle) == true ||
            listener.track?.artist?.lowercase()?.contains(needle) == true
    }

    LazyColumn(
        contentPadding = PaddingValues(
            start = design.screenPadding,
            end = design.screenPadding,
            top = 12.dp,
            bottom = 124.dp,
        ),
        verticalArrangement = Arrangement.spacedBy(design.gap),
    ) {
        item { ScreenTitle("Search", "Find a listener, a track or an artist") }

        item {
            OutlinedTextField(
                value = query,
                onValueChange = {
                    query = it
                    profile = null
                    message = null
                },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(if (design.ios) 18.dp else 20.dp),
                placeholder = { Text("username, track, artist", fontSize = 14.sp) },
                singleLine = true,
                textStyle = androidx.compose.ui.text.TextStyle(fontSize = 15.sp),
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
                keyboardActions = KeyboardActions(onSearch = { lookUp() }),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = design.accent,
                    unfocusedBorderColor = design.hairline,
                    focusedTextColor = design.fg,
                    unfocusedTextColor = design.fg,
                    cursorColor = design.accent,
                    focusedPlaceholderColor = design.dim,
                    unfocusedPlaceholderColor = design.dim,
                    focusedContainerColor = design.palette.bg2.copy(alpha = 0.35f),
                    unfocusedContainerColor = design.palette.bg2.copy(alpha = 0.35f),
                ),
            )
        }

        if (busy) {
            item { Text("Looking…", color = design.dim, fontSize = 13.sp) }
        }

        profile?.let { found ->
            item { SectionLabel("Profile") }
            item { ListenerCard(found) }
        }

        message?.let { text ->
            item {
                EmptyState(
                    icon = McIcon.Search,
                    title = "Nothing found",
                    body = text,
                )
            }
        }

        if (needle.isNotEmpty()) {
            item { SectionLabel("Active listeners") }
            if (matches.isEmpty()) {
                item {
                    EmptyState(
                        icon = McIcon.Search,
                        title = "No one matches",
                        body = "Search looks at the last three minutes of listening. Try a full username to look up a profile.",
                        actionLabel = "Look up \"${query.trim()}\"",
                        onAction = { lookUp() },
                    )
                }
            }
            items(matches, key = { it.username }) { ListenerCard(it) }
        } else if (directory.isNotEmpty()) {
            item { SectionLabel("Listening now") }
            items(directory.take(12), key = { it.username }) { ListenerCard(it) }
        }

        if (needle.isEmpty() && directory.isEmpty()) {
            item {
                EmptyState(
                    icon = McIcon.Search,
                    title = "Quiet on the server",
                    body = "Nobody is listening right now, so there is nothing to filter. Search a username to open their profile anyway.",
                )
            }
        }
    }
}
