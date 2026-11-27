# Signing key

`mcmusic.p12` is the only key that signs mcmusic APKs, on this machine and in
CI alike. It is committed on purpose.

Android refuses to install an update signed with a different key than the copy
already on the device — the install fails with "app conflicts with another
package", and the only way out is to uninstall, losing local settings. Before
this key existed, each build machine used its own auto-generated debug key, so
consecutive releases could not be installed over one another.

Keeping the key in the repository means any build, anywhere, produces an
installs-able update, and losing a developer laptop cannot orphan the install
base. The cost is that the key is public: anyone could sign an APK that claims
to be mcmusic. Since the app is free, sideloaded and holds no payment or
private data, and installs still require the user to open the file, that is a
trade worth making for updates that actually work.

Details: PKCS#12, alias `mcmusic`, store and key password `mcmusic` (see
`gui/android/app/build.gradle.kts`).

Do not regenerate or replace this file. A new key is a new app as far as
Android is concerned.

Because the key is public, an APK is trusted by its build checksum, not by who
could sign it: download `SHA256SUMS` from the same GitHub `latest` release, put
it beside the downloaded assets, run `sha256sum -c SHA256SUMS`, and compare the
APK's signing certificate fingerprint (`keytool -printcert -jarfile mcmusic.apk`)
with the fingerprint published on the releases page. The same digests are
recorded in the tracked text file `builds/release-manifest.json`. No binary is
kept in git. Publish that fingerprint with every release so users can make the
comparison.
