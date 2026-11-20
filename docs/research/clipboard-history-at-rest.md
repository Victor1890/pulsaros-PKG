# Clipboard History at rest: encrypt, memory-only, or plaintext

Ticket #181 (child of map #179). Research only; no decision is made here.

Scope: Spotlight Launcher Clipboard History (`pulsaros-spotlight-launcher/src/clipboard.rs`). Threat model: backups, disk theft, secrets lingering. Same-user malware is out of scope. Platform: Pulsar OS, GNOME 48/51, Wayland, Arch and Debian.

## 0. Current state (repo)

- Last 50 copies in `~/.local/share/pulsaros-spotlight/clipboard_history.json`, plaintext `serde_json::to_string_pretty`. File 0600 and dir 0700, written via a 0600 temp file plus rename (`write_private`, `ensure_private_dir`).
- Items capped at `MAX_ITEM_BYTES = 64 KiB`. Copies whose offer carries `x-kde-passwordManagerHint` are skipped (`has_secret_hint`).
- If the data dir cannot be resolved, history is already memory-only for that session (`data_dir: None`).
- Existing deps: `zbus 4.4`, `serde_json`, `rusqlite 0.32`, `libc`, `dirs`. No crypto or keyring crate yet.
- 0600/0700 does not help against backups that copy files, a stolen disk, or an unencrypted partition. It only blocks other local accounts.

## 1. What other tools do

| Tool | Storage | Encryption | Retention | Password-manager handling |
|---|---|---|---|---|
| Raycast (macOS) | local | "fully encrypted", "encrypted on your local hard drive" (vendor claim) | "kept until 3 months" | "Passwords copied from any password managers and other transient data are ignored by default" |
| GNOME Clipboard Indicator | JSON in `GLib.get_user_cache_dir()/<uuid>/` plus raw image files, backup `registry.txt~` | None. `JSON.stringify`, images raw bytes | `HISTORY_SIZE` setting (module default 15); oversized file (`CACHE_FILE_SIZE` MB) moved to backup keeping favorites; `CLEAR_ON_BOOT` and `CACHE_ONLY_FAVORITE` options | No `x-kde-passwordManagerHint` check. Only `PRIVATEMODE` and `EXCLUDED_APPS` (by window class) |
| Pano | SQLite (`DB_NAME=pano`, dir passed by caller), table `clipboard` | None visible: no key param on connection, `content` plain text | Not found in the files read | Skips content when offer has `x-kde-passwordManagerHint`; incognito toggle stops capture. README: "This project is no longer maintained" |
| GPaste | Pluggable: XML file, per-history SQLite, or nothing | Optional libsodium "Encryption at rest"; passphrase optionally kept in the keyring (build option `libsecret`, needs `encryption`); `gpaste-client change-passphrase`; both options default to `auto` | Not documented in README | `x-kde-passwordManagerHint` is taken in as a password, kept out of plain-text history, optional timeout |

Notes:
- Raycast is the only one that states encrypted storage, but it is marketing copy. Algorithm and key location for the clipboard DB are not documented for macOS. Raycast's developer security page says it "stores user data in a local encrypted database" and "makes use of the system Keychain where secure data is stored", which is general, not clipboard-specific. A Raycast Windows changelog (v0.23) mentions moving from a non-encrypted to an encrypted database.
- The two GNOME Shell extensions (Clipboard Indicator, Pano) are plaintext. GPaste is the only Linux example with optional encryption, and it keeps the passphrase in the keyring when available. Its README does not say what happens when the keyring is unavailable.
- Gap: I did not read GPaste source for its KDF/cipher or its keyring-unavailable path.

Sources:
- https://www.raycast.com/core-features/clipboard-history.md
- https://developers.raycast.com/information/security
- https://www.raycast.com/changelog/windows/0-23
- https://github.com/Tudmotu/gnome-shell-extension-clipboard-indicator (README, `registry.js`, `extension.js`)
- https://github.com/oae/gnome-shell-pano (README, `src/utils/db.ts`, `src/utils/clipboardManager.ts`)
- https://github.com/Keruspe/GPaste (README)

## 2. GNOME keyring: when is it unlocked?

Facts:
- The PAM module unlocks the `login` keyring with the password typed at login: "Upon authenticating the user, the PAM module tries to unlock the 'login' keyring with the password entered by the user." If `login` does not exist it is created with the user's password. https://wiki.gnome.org/Projects/GnomeKeyring/Pam
- Auto-login: no password passes through PAM, so the keyring is not unlocked. Reports: Arch bug FS#55950 (not unlocked on initial autologin), GNOME Shell issues 5610 and 2720 (prompt sometimes missing after autologin, Seahorse then cannot unlock). Ubuntu bug 1870628 treats the locked state as expected.
  - https://bugs.archlinux.org/task/55950
  - https://gitlab.gnome.org/GNOME/gnome-shell/-/issues/2720
  - https://gitlab.gnome.org/GNOME/gnome-shell/-/issues/5610
  - https://bugs.launchpad.net/ubuntu/+source/gnome-shell/+bug/1870628
- Common workaround: a blank keyring password so it unlocks without input. Trade-off: secrets in that keyring are then stored unencrypted on disk, so a key held there protects nothing against disk theft or backups. GNOME maintainers noted security implications (https://bugzilla.gnome.org/show_bug.cgi?id=621506). Known bug: blank password randomly reset to the user's password, bringing the prompt back (https://gitlab.gnome.org/GNOME/gnome-keyring/-/issues/79).
- Secret Service API: operations on a locked object fail with `org.freedesktop.Secret.Error.IsLocked` ("The object must be unlocked before this action can be carried out"). The spec has "Locking and Unlocking" and "Prompts and Prompting" sections, so a client can ask the service to unlock, which shows a prompt. My fetcher could not read those two sections; verify before relying on the exact flow. https://specifications.freedesktop.org/secret-service/latest/errors.html
- oo7 docs: on a locked collection, `search_items` / `items` "will return no items"; `unlock` takes an optional `WindowIdentifier`, suggesting a prompt. https://docs.rs/oo7/latest/oo7/dbus/struct.Collection.html
- A prompt at launcher start would be a modal from a launcher meant to appear instantly. Behavior on Wayland GNOME 48/51 is untested.

Not verified: behavior on the Pulsar OS image (display manager, whether `pam_gnome_keyring` is configured, whether the login keyring password is blank or the user's). Check on the image.

## 3. Rust options

Numbers from the crates.io API on 2026-11-20.

| Crate | Version | Recent downloads | What it is | Dep cost for this repo |
|---|---|---|---|---|
| `oo7` | 0.7.2, updated 2026-11-19 | 2.5M | Secret Service client (`dbus` backend) plus a libsecret-compatible encrypted file backend (portal key for sandboxed apps). Async only, tokio default, `async-std` opt-in. `native_crypto` default, `openssl_crypto` opt-in. Repo linux-credentials/oo7, MIT | Required deps include `zbus ^6`, `ashpd ^0.14`, `num-bigint-dig`, `zeroize`. Launcher uses `zbus 4.4`, so a second zbus major and ashpd come in |
| `secret-service` | 6.0.0-rc.1 (pre-release), updated 2026-11-06 | 13M | Secret Service client; async by default with a `blocking` module; optional crypto crates (`aes`, `cbc`, `hkdf`, `sha2`) or `openssl` | `zbus ^5` normal dep, another major than the launcher's 4.4. MIT OR Apache-2.0 |
| `keyring` | 4.2.0, updated 2026-08-29 | 20M | Cross-platform wrapper. Linux stores are optional deps: `dbus-secret-service-keyring-store`, `zbus-secret-service-keyring-store`, `linux-keyutils-keyring-store`, `db-keystore`. docs.rs page does not say which is default or what happens with no Secret Service | MIT OR Apache-2.0. Store selection to verify |
| `chacha20poly1305` | 0.11.0 | 120M total | RustCrypto AEAD, Apache-2.0 OR MIT | Small, pure Rust |
| `aes-gcm` | 0.11.1 | 221M total | RustCrypto AEAD, Apache-2.0 OR MIT | Small, pure Rust |

Also: the existing `zbus 4.4` dependency can call `org.freedesktop.secrets` directly with a hand-written proxy. That avoids a new crate but means implementing session/secret transfer and the prompt flow by hand.

Design shapes using these:
- A. File encrypted with an AEAD (ChaCha20-Poly1305 or AES-GCM), 32-byte random key stored as one Secret Service item (via oo7, secret-service or keyring). File = nonce plus ciphertext of the JSON. Adds one AEAD crate and one keyring crate.
- B. `oo7` file backend only: no D-Bus and no GNOME keyring. Per its docs the key can come from the Secrets portal for sandboxed apps; the key source for a non-sandboxed desktop app is to verify.
- C. Whole history as a Secret Service item. Avoids a file-crypto crate but ties every read and write to keyring availability; secret size limits not verified.
- D. User passphrase (GPaste-style). Poor UX for a launcher.

Sources:
- https://crates.io/api/v1/crates/oo7 , https://docs.rs/oo7/latest/oo7/ , https://crates.io/api/v1/crates/oo7/0.7.2/dependencies
- https://crates.io/api/v1/crates/secret-service , https://docs.rs/secret-service/latest/secret_service/
- https://crates.io/api/v1/crates/keyring , https://docs.rs/keyring/latest/keyring/
- https://crates.io/api/v1/crates/chacha20poly1305 , https://crates.io/api/v1/crates/aes-gcm

## 4. What breaks per option

| Scenario | Plaintext (today) | Memory-only | Encrypted file, key in keyring |
|---|---|---|---|
| After reboot or relogin | History survives | History lost, by design | Survives only if the key can be read. With autologin and a locked keyring the key is unreadable until unlocked |
| Launcher starts before keyring unlock | n/a | n/a | `IsLocked` or a prompt. Options: start empty and retry later, prompt, or fall back to memory-only. If the launcher generates a new key because it could not read the old one, the old file becomes unreadable and must be discarded |
| Keyring unavailable (no daemon, no `pam_gnome_keyring`) | Works | Works | No key: choose memory-only, plaintext fallback (defeats the goal), or refuse |
| Blank or no login password | Works | Works | Keyring effectively unencrypted on disk, so the key is as exposed as the file. No gain against disk theft |
| Backups and disk theft | Exposed (0600 does not stop it) | Protected, nothing on disk | Protected only if the keyring file is itself protected (real password) or not backed up with the history |
| Secrets lingering | On disk, up to 50 items | Gone at logout or reboot; still in RAM in session | Same lifetime as plaintext, encrypted on disk |
| Complexity and deps | none | least code (drop save/load) | AEAD crate plus keyring crate, key lifecycle, zbus major duplication |

Knobs that apply to any option (from the other tools): entry caps, clear on boot (Clipboard Indicator), time-based expiry (Raycast 3 months, GPaste password timeout), skip flagged secrets (already done). Under any encrypted or memory-only option, the existing plaintext `clipboard_history.json` needs a one-time migration and removal.

## 5. Open questions

1. On the Pulsar OS image: is `pam_gnome_keyring` configured, is autologin offered or default, and is the login keyring password blank or the user's?
2. Does an unlock prompt appear on GNOME 48/51 Wayland when requested by the launcher? Needs a test on the target image.
3. Is a second zbus major (5 or 6) acceptable in build time and size, or is a hand-written zbus 4.4 proxy preferred?
4. GPaste source: KDF, cipher, and keyring-unavailable behavior (not read).
