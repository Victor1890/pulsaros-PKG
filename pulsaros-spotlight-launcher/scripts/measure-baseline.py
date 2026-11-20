#!/usr/bin/env python3
"""Baseline measurements for the Pulsar OS Spotlight Launcher.

Run on a Pulsar OS GNOME session (VM, plus real hardware if you can). Python 3 stdlib plus
PyGObject (`gi`) for D-Bus; without `gi` it falls back to `gdbus` and measures coarser.

  measure-baseline.py env                    environment facts only
  measure-baseline.py show   [--runs 20]     Show Latency, cold and warm
  measure-baseline.py search [--runs 20]     Search Latency of the backend paths
  measure-baseline.py idle   [--duration 300] Idle Cost of the hidden Launcher
  measure-baseline.py all                    env + show + search + idle

Results go to ./baseline-results/<UTC time>-<host>/results.json and results.md. Paste results.md
into the ticket. Every number is wall-clock on this machine: compare runs on the same machine.

What this does NOT measure: UI rendering of result rows and the time until the text field accepts
keys. Show Latency here is "process/activation start until the window is listed by the Shell
Extension". See the end of this file for the optional screen-recording check.
"""
import argparse
import json
import os
import platform
import shutil
import socket
import sqlite3
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BIN = "pulsaros-spotlight"
APP_ID = "es.inled.pulsaros-spotlight"
WIN_NAME, WIN_PATH = "es.inled.PulsarosSpotlight.Windows", "/es/inled/PulsarosSpotlight/Windows"
CTL_NAME, CTL_PATH = "es.inled.PulsarosSpotlight.Control", "/es/inled/PulsarosSpotlight/Control"
NAUTILUS = ("org.gnome.Nautilus", "/org/gnome/Nautilus/SearchProvider", "org.gnome.Shell.SearchProvider2")
QUERIES = ["a", "re", "rep", "repo", "report", "firefox", "pdf", "2024", "settings"]

try:
    import gi

    gi.require_version("Gio", "2.0")
    from gi.repository import Gio, GLib

    HAVE_GI = True
except Exception:  # noqa: BLE001
    HAVE_GI = False


def stats(xs):
    """Summary of a list of millisecond samples."""
    if not xs:
        return {"n": 0}
    s = sorted(xs)
    p95 = s[min(len(s) - 1, int(round(0.95 * (len(s) - 1))))]
    return {"n": len(s), "min": round(s[0], 2), "median": round(statistics.median(s), 2),
            "p95": round(p95, 2), "max": round(s[-1], 2)}


def sh(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


# ---- D-Bus -------------------------------------------------------------------------------
class Bus:
    """Session-bus calls. Uses Gio when available (sub-millisecond), else the gdbus CLI."""

    def __init__(self):
        self.conn = Gio.bus_get_sync(Gio.BusType.SESSION, None) if HAVE_GI else None

    def call(self, dest, path, iface, method, params=None, reply="()"):
        """Returns the unpacked reply, or raises."""
        if self.conn:
            r = self.conn.call_sync(dest, path, iface, method, params,
                                    GLib.VariantType(reply), Gio.DBusCallFlags.NONE, 2000, None)
            return r.unpack()
        args = [] if params is None else [str(params)]
        out = subprocess.run(["gdbus", "call", "--session", "--dest", dest, "--object-path", path,
                              "--method", f"{iface}.{method}", *args],
                             capture_output=True, text=True, timeout=5, check=True).stdout
        return out

    def windows(self):
        """Rows (id, title, wm_class, app_id, workspace) from the Shell Extension, or None."""
        try:
            r = self.call(WIN_NAME, WIN_PATH, WIN_NAME, "ListWindows", None, "(a(ussss))")
        except Exception:  # noqa: BLE001
            return None
        if isinstance(r, str):  # gdbus fallback: text only
            return [(0, "Spotlight", "", "", "")] if ("Spotlight" in r or APP_ID in r) else []
        return r[0]

    def has_spotlight_window(self):
        rows = self.windows()
        if rows is None:
            return None
        return any(t == "Spotlight" or c in ("pulsaros-spotlight", "spotlight-gtk") or a == APP_ID
                   for (_i, t, c, a, _w) in rows)


def instance_pids():
    out = sh(["pgrep", "-x", BIN])
    return [int(p) for p in out.split()] if out else []


# ---- env ---------------------------------------------------------------------------------
def env_info():
    cpu = ""
    try:
        for line in open("/proc/cpuinfo"):
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    mem = 0
    try:
        for line in open("/proc/meminfo"):
            if line.startswith("MemTotal"):
                mem = int(line.split()[1]) // 1024
                break
    except OSError:
        pass
    pkg = sh(["pacman", "-Q", "pulsaros-spotlight-launcher"]) or \
        sh(["dpkg-query", "-W", "-f=${Package} ${Version}", "pulsaros-spotlight-launcher"])
    return {
        "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "host": socket.gethostname(),
        "virt": sh(["systemd-detect-virt"]) or "none/unknown",
        "kernel": platform.release(),
        "cpu": cpu, "cpus": os.cpu_count(), "mem_mb": mem,
        "gnome_shell": sh(["gnome-shell", "--version"]),
        "session_type": os.environ.get("XDG_SESSION_TYPE", ""),
        "package": pkg,
        "binary": shutil.which(BIN) or "NOT FOUND",
        "extension_windows_api": None,  # filled by `show`
        "have_gi": HAVE_GI,
    }


# ---- show --------------------------------------------------------------------------------
def wait_for(pred, timeout):
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout:
        if pred():
            return (time.perf_counter() - t0) * 1000
        time.sleep(0.002)
    return None


def measure_show(runs, kill_existing):
    bus = Bus()
    res = {"cold_ms": [], "warm_ms": [], "notes": []}
    if bus.windows() is None:
        res["notes"].append("Shell Extension Windows API not reachable: enable "
                            "pulsaros-spotlight-launcher@inled.es and re-run. Show not measured.")
        return res
    if instance_pids():
        if not kill_existing:
            res["notes"].append("A pulsaros-spotlight instance is already running; re-run with "
                                "--kill-existing to let this script stop it.")
            return res
        subprocess.run(["pkill", "-x", BIN])
        wait_for(lambda: not instance_pids(), 5)

    for i in range(runs):  # cold: no resident process
        t0 = time.perf_counter()
        p = subprocess.Popen([BIN], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        t = wait_for(lambda: bus.has_spotlight_window(), 10)
        if t is None:
            res["notes"].append(f"cold run {i}: window never listed within 10 s")
        else:
            res["cold_ms"].append((time.perf_counter() - t0) * 1000)
        p.terminate()
        try:
            p.wait(5)
        except subprocess.TimeoutExpired:
            p.kill()
        wait_for(lambda: not instance_pids(), 5)
        time.sleep(0.3)

    resident = subprocess.Popen([BIN, "--hidden"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)  # let the resident instance finish startup
    try:
        for i in range(runs):  # warm: activate the resident instance
            if bus.has_spotlight_window():  # hide it first
                try:
                    bus.call(CTL_NAME, CTL_PATH, CTL_NAME, "Hide")
                except Exception:  # noqa: BLE001
                    pass
                wait_for(lambda: not bus.has_spotlight_window(), 2)
                time.sleep(0.3)
            t0 = time.perf_counter()
            subprocess.Popen([BIN], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            t = wait_for(lambda: bus.has_spotlight_window(), 5)
            if t is None:
                res["notes"].append(f"warm run {i}: window never listed within 5 s "
                                    "(it may be hidden by focus loss or skip the taskbar list)")
            else:
                res["warm_ms"].append((time.perf_counter() - t0) * 1000)
    finally:
        resident.terminate()
    return res


# ---- search ------------------------------------------------------------------------------
def time_calls(fn, runs):
    out = []
    for _ in range(runs):
        t0 = time.perf_counter()
        fn()
        out.append((time.perf_counter() - t0) * 1000)
    return out


def measure_search(runs, queries):
    bus = Bus()
    res = {"dbus_overhead_ms": {}, "nautilus": {}, "fallback_walk": {}, "browser_history": {}, "notes": []}

    # constant cost of one D-Bus round trip, to subtract from the Nautilus numbers
    try:
        res["dbus_overhead_ms"] = stats(time_calls(
            lambda: bus.call("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus.Peer",
                             "Ping", None, "()"), runs))
    except Exception as e:  # noqa: BLE001
        res["notes"].append(f"D-Bus ping failed: {e}")

    for q in queries:
        try:
            if HAVE_GI:
                params = GLib.Variant("(as)", ([q],))
                first = bus.call(*NAUTILUS[:3], "GetInitialResultSet", params, "(as)")
                n = len(first[0])
                ms = time_calls(lambda: bus.call(*NAUTILUS[:3], "GetInitialResultSet", params, "(as)"), runs)
            else:
                n = None
                ms = time_calls(lambda: bus.call(*NAUTILUS[:3], "GetInitialResultSet", f"['{q}']"), runs)
            res["nautilus"][q] = {**stats(ms), "results": n}
        except Exception as e:  # noqa: BLE001
            res["nautilus"][q] = {"error": str(e)[:120]}

    # same walk as search.rs fallback_file_search: 6 roots, depth 3, substring, limit 500
    home = Path.home()
    roots = [home / d for d in ("Documents", "Downloads", "Pictures", "Music", "Videos", "Desktop")]

    def walk(d, q, depth, found, seen):
        if depth > 3 or len(found) >= 500:
            return
        try:
            entries = list(os.scandir(d))
        except OSError:
            return
        for e in entries:
            seen[0] += 1
            n = e.name
            if n.startswith(".") or n in ("node_modules", "target"):
                continue
            if q in n.lower():
                found.append(e.path)
            try:
                if e.is_dir(follow_symlinks=False):
                    walk(e.path, q, depth + 1, found, seen)
            except OSError:
                pass

    for q in queries:
        seen = [0]

        def run():
            seen[0] = 0
            found = []
            for r in roots:
                if r.is_dir():
                    walk(r, q, 0, found, seen)

        ms = time_calls(run, max(3, runs // 4))
        res["fallback_walk"][q] = {**stats(ms), "entries_visited": seen[0]}

    # Firefox history, same SQL as search.rs query_browser_history_plain
    dbs = list((home / ".mozilla/firefox").glob("*/places.sqlite")) + \
        [home / ".mozilla/seafari-profile/places.sqlite"]
    dbs = [d for d in dbs if d.is_file()]
    if not dbs:
        res["notes"].append("no Firefox places.sqlite found: browser_history not measured")
    for db in dbs:
        per = {}
        for q in queries:
            def one():
                c = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=0.1)
                try:
                    c.execute("SELECT url,title FROM moz_places WHERE (title LIKE ? OR url LIKE ?) "
                              "AND hidden=0 ORDER BY frecency DESC LIMIT 6", (f"%{q}%", f"%{q}%")).fetchall()
                finally:
                    c.close()
            try:
                per[q] = stats(time_calls(one, runs))
            except sqlite3.OperationalError as e:
                per[q] = {"error": str(e)}
        res["browser_history"][str(db)] = per
    return res


# ---- idle --------------------------------------------------------------------------------
def proc_sample(pid):
    ctx_v = ctx_n = threads = 0
    for t in Path(f"/proc/{pid}/task").iterdir():
        try:
            for line in open(t / "status"):
                if line.startswith("voluntary_ctxt_switches"):
                    ctx_v += int(line.split()[1])
                elif line.startswith("nonvoluntary_ctxt_switches"):
                    ctx_n += int(line.split()[1])
            threads += 1
        except OSError:
            pass
    st = open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()
    ticks = int(st[11]) + int(st[12])  # utime + stime
    rss = 0
    for line in open(f"/proc/{pid}/status"):
        if line.startswith("VmRSS"):
            rss = int(line.split()[1])
    return {"t": time.monotonic(), "ctx_v": ctx_v, "ctx_n": ctx_n, "ticks": ticks, "rss_kb": rss,
            "threads": threads}


def measure_idle(duration, pid=None):
    res = {"notes": []}
    started = None
    if pid is None:
        pids = instance_pids()
        if pids:
            pid = pids[0]
            res["notes"].append("measured the already-running instance")
        else:
            started = subprocess.Popen([BIN, "--hidden"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            pid = started.pid
            time.sleep(5)  # settle after startup
            res["notes"].append("started a hidden instance for the measurement")
    try:
        a = proc_sample(pid)
        time.sleep(duration)
        b = proc_sample(pid)
    finally:
        if started:
            started.terminate()
    dt = b["t"] - a["t"]
    hz = os.sysconf("SC_CLK_TCK")
    res.update({
        "pid": pid, "seconds": round(dt, 1), "threads": b["threads"],
        "wakeups_per_s": round((b["ctx_v"] - a["ctx_v"]) / dt, 2),
        "involuntary_switches_per_s": round((b["ctx_n"] - a["ctx_n"]) / dt, 2),
        "cpu_percent": round(100.0 * (b["ticks"] - a["ticks"]) / hz / dt, 3),
        "rss_mb_start": round(a["rss_kb"] / 1024, 1), "rss_mb_end": round(b["rss_kb"] / 1024, 1),
    })
    res["notes"].append("wakeups_per_s = voluntary context switches summed over all threads: a "
                        "thread that blocks again after each wake. It approximates timer and event "
                        "wakeups; it is not a direct hardware wakeup count.")
    return res


# ---- report ------------------------------------------------------------------------------
def row(label, s):
    if "error" in s:
        return f"| {label} | error | | | {s['error']} |"
    return f"| {label} | {s['n']} | {s['median']} | {s['p95']} | {s['max']} |"


def markdown(r):
    L = ["# Spotlight Launcher baseline", ""]
    e = r["env"]
    L += [f"- Date (UTC): {e['utc']}", f"- Host: {e['host']} ({e['virt']}), {e['cpus']} CPUs, {e['mem_mb']} MB",
          f"- CPU: {e['cpu']}", f"- Kernel: {e['kernel']}", f"- GNOME Shell: {e['gnome_shell']}",
          f"- Session: {e['session_type']}", f"- Package: {e['package'] or 'unknown'}", f"- Binary: {e['binary']}", ""]
    if "show" in r:
        L += ["## Show Latency (ms, process or activation start until window is listed)", "",
              "| Case | n | median | p95 | max |", "|---|---|---|---|---|",
              row("cold start", stats(r["show"]["cold_ms"])), row("warm (resident)", stats(r["show"]["warm_ms"])), ""]
        L += [f"- {n}" for n in r["show"]["notes"]] + [""]
    if "search" in r:
        s = r["search"]
        L += ["## Search Latency (ms per query)", "", f"D-Bus round trip overhead: {s['dbus_overhead_ms']}", "",
              "### Nautilus search provider", "", "| Query | n | median | p95 | max |", "|---|---|---|---|---|"]
        L += [row(f"`{q}` ({v.get('results')} results)", v) for q, v in s["nautilus"].items()]
        L += ["", "### Fallback home-folder walk (runs when Nautilus returns nothing)", "",
              "| Query | n | median | p95 | max |", "|---|---|---|---|---|"]
        L += [row(f"`{q}` ({v['entries_visited']} entries)", v) for q, v in s["fallback_walk"].items()]
        for db, per in s["browser_history"].items():
            L += ["", f"### Firefox history `{db}`", "", "| Query | n | median | p95 | max |", "|---|---|---|---|---|"]
            L += [row(f"`{q}`", v) for q, v in per.items()]
        L += [""] + [f"- {n}" for n in s["notes"]] + [""]
    if "idle" in r:
        i = r["idle"]
        L += ["## Idle Cost", ""]
        for k in ("seconds", "threads", "wakeups_per_s", "involuntary_switches_per_s", "cpu_percent",
                  "rss_mb_start", "rss_mb_end"):
            if k in i:
                L.append(f"- {k}: {i[k]}")
        L += [""] + [f"- {n}" for n in i["notes"]] + [""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["env", "show", "search", "idle", "all"])
    ap.add_argument("--runs", type=int, default=20)
    ap.add_argument("--duration", type=int, default=300, help="idle seconds")
    ap.add_argument("--queries", nargs="*", default=QUERIES)
    ap.add_argument("--kill-existing", action="store_true", help="let `show` stop a running instance")
    ap.add_argument("--out", default="baseline-results")
    a = ap.parse_args()

    r = {"env": env_info()}
    if r["env"]["binary"] == "NOT FOUND" and a.cmd in ("show", "idle", "all"):
        sys.exit(f"{BIN} not found in PATH")
    if a.cmd in ("show", "all"):
        r["show"] = measure_show(a.runs, a.kill_existing)
        r["env"]["extension_windows_api"] = not any("not reachable" in n for n in r["show"]["notes"])
    if a.cmd in ("search", "all"):
        r["search"] = measure_search(a.runs, a.queries)
    if a.cmd in ("idle", "all"):
        r["idle"] = measure_idle(a.duration)

    d = Path(a.out) / f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{r['env']['host']}"
    d.mkdir(parents=True, exist_ok=True)
    (d / "results.json").write_text(json.dumps(r, indent=2))
    md = markdown(r)
    (d / "results.md").write_text(md)
    print(md)
    print(f"\nWritten to {d}/results.md and results.json")


if __name__ == "__main__":
    main()

# Optional end-to-end check (not automated): record the screen at 60 fps with GNOME's screencast
# (Ctrl+Shift+Alt+R), press the Spotlight shortcut, type "repo", stop. Step through the video
# frame by frame (for example `mpv --frame-step`) and count frames from the key press to (a) the
# window appearing and (b) the first result row. At 60 fps one frame is 16.7 ms.
