# Linking Rotur without the web UI

mcmusic normally links Rotur through OAuth in a browser. API clients — a TUI, a
bot, a script, anything that is not the official app — can link with a **key +
validator** instead. No browser, cookie, or official client is involved.

The flow is:

1. Read the server's Rotur key.
2. Mint a validator for that key with the person's Rotur token.
3. Send the validator to mcmusic with an mcmusic API token.

The server asks Rotur who owns the validator, then stores the Rotur id and
username on the mcmusic account. mcmusic never sees the person's Rotur token
unless they choose to send it for activity support.

## 0. Get an mcmusic session

Any of the normal API credentials works, so a TUI needs nothing special:

```sh
# password login, keeping the session cookie in a jar
curl -s -c mc.cookies -X POST https://music.example.com/api/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"you","password":"…"}'
```

Pass `-b mc.cookies` on the calls below. If the client would rather carry a
bearer token, mint one from an authenticated session with
`POST /api/devices/code` followed by `POST /api/devices/claim`, then send
`Authorization: Bearer mcd_…`.

## 1. Get the key

```sh
curl -s https://music.example.com/api/auth/rotur/key
```

```json
{
  "configured": true,
  "key": "app_0123456789abcdef",
  "app": "app_0123456789abcdef",
  "mint": "POST https://api.rotur.dev/v2/validators?key=app_0123456789abcdef",
  "verify": "GET https://api.rotur.dev/v2/validators/verify?v=<validator>&key=app_0123456789abcdef",
  "link": "https://music.example.com/api/auth/rotur/link",
  "header": "X-Rotur-Validator",
  "body": { "validator": "<validator>" }
}
```

This endpoint is public. The key is the Rotur app id, which is not a secret.

## 2. Mint a validator

Use the person's Rotur access token. A Sign in with Rotur token can mint a
validator for its own app; any other token needs the `validators:generate`
permission.

```sh
curl -s -X POST "https://api.rotur.dev/v2/validators?key=app_0123456789abcdef" \
  -H "Authorization: Bearer $ROTUR_TOKEN"
```

```json
{ "validator": "7ebdf483-5b9f-4b70-9edc-a1f2827391f9,9c1f…" }
```

Validators last five minutes. Reuse one for that window.

## 3. Link it

Authenticate as the mcmusic user with a device/API token
(`Authorization: Bearer mcd_…`) or a session cookie, and send the validator in
`X-Rotur-Validator` or the JSON body.

```sh
curl -s -X POST "https://music.example.com/api/auth/rotur/link" \
  -H "Authorization: Bearer $MCMUSIC_TOKEN" \
  -H "X-Rotur-Validator: $VALIDATOR" \
  -H "Content-Type: application/json" \
  -d '{"validator":"'"$VALIDATOR"'"}'
```

```json
{
  "ok": true,
  "linked": true,
  "rotur_id": "7ebdf483-5b9f-4b70-9edc-a1f2827391f9",
  "rotur_username": "cardinal",
  "expires_at": 1790000300000,
  "account_type": null,
  "owner": null,
  "has_tokens": false
}
```

If the same account was linked to a different Rotur identity, the old link and
its activity session are cleared first.

### Optional: enable Rotur activity

A validator proves identity but cannot post activity. To let mcmusic publish
the current track as a Rotur listening activity, also send the person's Rotur
access token. It must belong to the same Rotur account.

```sh
curl -s -X POST "https://music.example.com/api/auth/rotur/link" \
  -H "Authorization: Bearer $MCMUSIC_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"validator":"'"$VALIDATOR"'","token":"'"$ROTUR_TOKEN"'"}'
```

The token is stored server-side; `has_tokens` is `true` in the response.

## Errors

| Status | `code` | Meaning |
| --- | --- | --- |
| 400 | `validator_required` | No validator was sent. |
| 400 | `rotur_token_mismatch` | The optional token belongs to another Rotur account. |
| 401 | `login_required` | The mcmusic API token was missing or invalid. |
| 401 | `invalid_validator` | Rotur rejected the validator (wrong key, expired, or malformed). |
| 401 | `app_banned`, `app_suspended`, … | Rotur says this account may not use the app. Show `error`. |
| 401 | `rotur_token_invalid` | The optional token was rejected by Rotur. |
| 409 | `rotur_already_linked` | That Rotur account belongs to a different mcmusic user. |
| 502 | `rotur_unreachable` | Rotur could not be reached. Try again. |

## Check and unlink

The existing endpoints work with the same API token:

```sh
curl -s https://music.example.com/api/auth/rotur/status \
  -H "Authorization: Bearer $MCMUSIC_TOKEN"

curl -s -X POST https://music.example.com/api/auth/rotur/unlink \
  -H "Authorization: Bearer $MCMUSIC_TOKEN"
```

`status` returns `linked`, `rotur_id`, `rotur_username`, and whether activity
tokens are present. `unlink` removes the Rotur id and any stored session.
