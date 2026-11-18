use crate::config::SpotlightConfig;
use crate::search::SearchResult;
use gtk4::gdk;
use gtk4::prelude::*;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::sync::{Arc, Mutex};
use std::time::SystemTime;

/// Largest clipboard entry kept in history; longer text is cut on a char boundary.
pub const MAX_ITEM_BYTES: usize = 64 * 1024;
const SECRET_HINT_MIME: &str = "x-kde-passwordManagerHint";

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct ClipboardItem {
    pub text: String,
    pub timestamp: f64,
}

#[derive(Clone)]
pub struct ClipboardManager {
    inner: Arc<Mutex<ClipboardManagerInner>>,
    /// Background writer; `None` when history is in-memory only.
    writer: Option<std::sync::mpsc::Sender<WriterMsg>>,
}

/// Messages for the background history writer.
enum WriterMsg {
    /// Latest snapshot to persist; bursts are coalesced into one write.
    Save(Vec<ClipboardItem>),
    /// Write any pending snapshot now, then signal.
    Flush(std::sync::mpsc::Sender<()>),
}

/// Quiet period after the last change before a snapshot is written.
const SAVE_DEBOUNCE: std::time::Duration = std::time::Duration::from_millis(250);

struct ClipboardManagerInner {
    items: Vec<ClipboardItem>,
    /// Lowercased copy of each item's text (same order), so search doesn't re-lowercase per keystroke.
    lower: Vec<String>,
    config: SpotlightConfig,
    /// Resolved data directory for this session; `None` means the platform
    /// data-directory lookup failed, so history stays in-memory only.
    data_dir: Option<PathBuf>,
}

impl ClipboardManager {
    fn data_dir() -> Option<PathBuf> {
        dirs::data_dir().map(|d| d.join("pulsaros-spotlight"))
    }

    fn clipboard_file_in(dir: &PathBuf) -> PathBuf {
        dir.join("clipboard_history.json")
    }

    pub fn new(config: SpotlightConfig) -> Self {
        Self::new_internal(config, Self::data_dir())
    }

    /// Test-only constructor that pins the data directory instead of resolving
    /// the real platform one, so tests never touch the user's actual files.
    #[cfg(test)]
    fn new_for_test(config: SpotlightConfig, dir: PathBuf) -> Self {
        Self::new_internal(config, Some(dir))
    }

    fn new_internal(config: SpotlightConfig, dir: Option<PathBuf>) -> Self {
        let mut items = Vec::new();
        match &dir {
            Some(dir) => {
                let file = Self::clipboard_file_in(dir);
                if file.exists() {
                    if let Ok(content) = fs::read_to_string(&file) {
                        if let Ok(loaded) = serde_json::from_str::<Vec<ClipboardItem>>(&content) {
                            items = loaded;
                        }
                    }
                }
            }
            None => {
                eprintln!(
                    "pulsaros-spotlight: could not resolve data directory; clipboard history will not persist this session"
                );
            }
        }

        let lower = items.iter().map(|i| i.text.to_lowercase()).collect();
        let writer = dir.clone().map(Self::spawn_writer);
        let inner = Arc::new(Mutex::new(ClipboardManagerInner { items, lower, config, data_dir: dir }));
        Self { inner, writer }
    }

    /// Starts the writer thread. It waits for a quiet period after the last snapshot so a burst
    /// of copies costs one write, and exits when every manager clone is dropped.
    fn spawn_writer(dir: PathBuf) -> std::sync::mpsc::Sender<WriterMsg> {
        use std::sync::mpsc::{channel, RecvTimeoutError};
        let (tx, rx) = channel::<WriterMsg>();
        std::thread::spawn(move || {
            let write = |items: &Vec<ClipboardItem>| Self::persist(&dir, items);
            let mut pending: Option<Vec<ClipboardItem>> = None;
            loop {
                let msg = if pending.is_some() {
                    match rx.recv_timeout(SAVE_DEBOUNCE) {
                        Ok(m) => Some(m),
                        Err(RecvTimeoutError::Timeout) => None,
                        Err(RecvTimeoutError::Disconnected) => {
                            if let Some(items) = pending.take() {
                                write(&items);
                            }
                            return;
                        }
                    }
                } else {
                    match rx.recv() {
                        Ok(m) => Some(m),
                        Err(_) => return,
                    }
                };
                match msg {
                    Some(WriterMsg::Save(items)) => pending = Some(items),
                    Some(WriterMsg::Flush(ack)) => {
                        if let Some(items) = pending.take() {
                            write(&items);
                        }
                        let _ = ack.send(());
                    }
                    None => {
                        if let Some(items) = pending.take() {
                            write(&items);
                        }
                    }
                }
            }
        });
        tx
    }

    /// Writes any pending history to disk now. Call before the process exits.
    pub fn flush(&self) {
        if let Some(tx) = &self.writer {
            let (ack_tx, ack_rx) = std::sync::mpsc::channel();
            if tx.send(WriterMsg::Flush(ack_tx)).is_ok() {
                let _ = ack_rx.recv_timeout(std::time::Duration::from_secs(5));
            }
        }
    }

    /// Persists the current history synchronously. Used by tests and shutdown; normal
    /// changes go through the background writer instead.
    pub fn save(&self) {
        let inner = self.inner.lock().unwrap();
        let Some(dir) = inner.data_dir.clone() else { return };
        Self::persist(&dir, &inner.items);
    }

    fn persist(dir: &std::path::Path, items: &Vec<ClipboardItem>) {
        if Self::ensure_private_dir(dir).is_err() {
            return;
        }
        let file = Self::clipboard_file_in(&dir.to_path_buf());
        if let Ok(content) = serde_json::to_string_pretty(items) {
            let _ = Self::write_private(&file, content.as_bytes());
        }
    }

    /// Creates `dir` (and parents) and locks it to 0700, so other local accounts
    /// can't list or traverse it, whatever the umask or a previous version left.
    fn ensure_private_dir(dir: &std::path::Path) -> std::io::Result<()> {
        use std::os::unix::fs::{DirBuilderExt, PermissionsExt};
        fs::DirBuilder::new().recursive(true).mode(0o700).create(dir)?;
        fs::set_permissions(dir, fs::Permissions::from_mode(0o700))
    }

    /// Writes `bytes` to a 0600 temp file created with that mode (never readable by
    /// others, even briefly) and renames it over `path`, which also tightens a
    /// pre-existing looser file.
    fn write_private(path: &std::path::Path, bytes: &[u8]) -> std::io::Result<()> {
        use std::io::Write;
        use std::os::unix::fs::OpenOptionsExt;
        let tmp = path.with_extension("json.tmp");
        let _ = fs::remove_file(&tmp);
        let mut f = fs::OpenOptions::new().write(true).create_new(true).mode(0o600).open(&tmp)?;
        f.write_all(bytes)?;
        drop(f);
        fs::rename(&tmp, path)
    }

    /// True when the clipboard offer marks its content as secret (password managers set
    /// `x-kde-passwordManagerHint`), so history must not record it.
    pub fn has_secret_hint<S: AsRef<str>>(mime_types: &[S]) -> bool {
        mime_types.iter().any(|m| m.as_ref() == SECRET_HINT_MIME)
    }

    /// Records `text` unless the offer's mime types flag it as a secret.
    pub fn record_clip_with_formats<S: AsRef<str>>(&self, text: &str, mime_types: &[S]) {
        if Self::has_secret_hint(mime_types) {
            return;
        }
        self.record_clip(text);
    }

    pub fn record_clip(&self, text: &str) {
        let mut clean = text.trim();
        if clean.is_empty() {
            return;
        }
        if clean.len() > MAX_ITEM_BYTES {
            let mut end = MAX_ITEM_BYTES;
            while !clean.is_char_boundary(end) {
                end -= 1;
            }
            clean = &clean[..end];
        }

        let mut inner = self.inner.lock().unwrap();
        // Avoid duplicate at top
        if let Some(first) = inner.items.first() {
            if first.text == clean {
                return;
            }
        }

        // Remove previous occurrences
        let keep: Vec<bool> = inner.items.iter().map(|item| item.text != clean).collect();
        let mut k = keep.iter();
        inner.items.retain(|_| *k.next().unwrap());
        let mut k = keep.iter();
        inner.lower.retain(|_| *k.next().unwrap());

        let timestamp = SystemTime::now()
            .duration_since(SystemTime::UNIX_EPOCH)
            .map(|d| d.as_secs_f64())
            .unwrap_or(0.0);

        inner.lower.insert(0, clean.to_lowercase());
        inner.items.insert(0, ClipboardItem {
            text: clean.to_string(),
            timestamp,
        });

        // Enforce max items
        let max_items = inner.config.clipboard_max_items;
        if inner.items.len() > max_items {
            inner.items.truncate(max_items);
            inner.lower.truncate(max_items);
        }

        // Hand a snapshot to the background writer; never block the caller on disk I/O.
        let snapshot = inner.items.clone();
        drop(inner);
        if let Some(tx) = &self.writer {
            let _ = tx.send(WriterMsg::Save(snapshot));
        }
    }

    pub fn get_items(&self) -> Vec<ClipboardItem> {
        self.inner.lock().unwrap().items.clone()
    }

    pub fn get_clip_by_index(&self, index: usize) -> Option<String> {
        let inner = self.inner.lock().unwrap();
        inner.items.get(index).map(|item| item.text.clone())
    }

    pub fn search_history(&self, query: &str) -> Vec<SearchResult> {
        let inner = self.inner.lock().unwrap();
        let items = &inner.items;
        let q_lower = query.trim().to_lowercase();
        let mut results = Vec::new();

        for (idx, item) in items.iter().enumerate() {
            if q_lower.is_empty() || inner.lower[idx].contains(&q_lower) {
                let lines: Vec<&str> = item.text.lines().map(|l| l.trim()).filter(|l| !l.is_empty()).collect();
                let mut first_line = lines.first().copied().unwrap_or(&item.text).to_string();
                if first_line.chars().count() > 60 {
                    first_line = first_line.chars().take(57).collect::<String>() + "...";
                }

                let mut preview = item.text.replace('\n', " ⏎ ");
                if preview.chars().count() > 100 {
                    preview = preview.chars().take(97).collect::<String>() + "...";
                }

                results.push(SearchResult {
                    url: format!("clipboard://{}", idx),
                    title: first_line,
                    mime: "text/plain-clipboard".to_string(),
                    snippet: preview,
                    app: None,
                });
            }
        }

        results
    }

    pub fn paste_clip(&self, text: &str) {
        if text.is_empty() {
            return;
        }

        // 1. Set to Gdk Clipboard
        if let Some(display) = gdk::Display::default() {
            display.clipboard().set_text(text);
        }

        // 2. Run wl-copy in background
        if let Ok(mut child) = Command::new("wl-copy")
            .stdin(Stdio::piped())
            .spawn()
        {
            if let Some(mut stdin) = child.stdin.take() {
                use std::io::Write;
                let _ = stdin.write_all(text.as_bytes());
            }
        }

        // 3. Simulate Paste (Ctrl+V) after window hides
        let auto_paste = self.inner.lock().unwrap().config.clipboard_auto_paste;
        if auto_paste {
            gtk4::glib::timeout_add_local(std::time::Duration::from_millis(100), move || {
                Self::simulate_paste();
                gtk4::glib::ControlFlow::Break
            });
        }
    }

    fn simulate_paste() {
        let which = |cmd: &str| -> Option<PathBuf> {
            std::env::var_os("PATH").and_then(|paths| {
                std::env::split_paths(&paths).filter_map(|dir| {
                    let full_path = dir.join(cmd);
                    if full_path.is_file() {
                        Some(full_path)
                    } else {
                        None
                    }
                }).next()
            })
        };

        // 1. Native Wayland uinput via ydotool
        if let Some(path) = which("ydotool") {
            let uid = unsafe { libc::getuid() };
            let sock = format!("/run/user/{}/.ydotool_socket", uid);
            let mut cmd = Command::new(path);
            cmd.args(&["key", "29:1", "47:1", "47:0", "29:0"]);
            if std::path::Path::new(&sock).exists() {
                cmd.env("YDOTOOL_SOCKET", sock);
            }
            if cmd.spawn().is_ok() {
                return;
            }
        }

        // 2. GNOME Shell Extension D-Bus key injection
        if let Ok(conn) = zbus::blocking::Connection::session() {
            let body = zbus::zvariant::Value::from(""); // empty or dummy
            // Make session call
            if conn.call_method(
                Some("org.gnome.Shell.Extensions.PulsarSpotlight"),
                "/org/gnome/Shell/Extensions/PulsarSpotlight",
                Some("org.gnome.Shell.Extensions.PulsarSpotlight"),
                "Paste",
                &body,
            ).is_ok() {
                return;
            }
        }

        // 3. Fallback: xdotool
        if let Some(path) = which("xdotool") {
            let _ = Command::new(path)
                .args(&["key", "ctrl+v"])
                .spawn();
        }
    }
}

#[cfg(test)]
#[path = "tests/clipboard_tests.rs"]
mod tests;
