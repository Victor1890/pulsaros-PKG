# Arch ISO guest facts (GNOME, BlueZ, session)

Answers Victor1890/pulsaros-PKG#147 (map: #145, blocks #150).

Subject: `ISO/build/pulsaros-stable-arch-grub.iso`, built 2026-11-12 (`BUILD_ID=202611121340`), booted by `ISO/run-qemu.sh`.
Method: read-only listing and extraction of small files from the ISO's root image
(`ISO/build/pulsaros-stable-arch-grub.squashfs`; the ISO's `arch/x86_64/airootfs.sfs` has the same size, 2703527936 bytes, and mtime, and `live/x86_64/airootfs.sfs` is a hard link to it)
plus `ISO/build-iso.sh`, `ISO/run-qemu.sh` and the package sources in this repo. Nothing was booted. Every runtime claim below is inferred from files, not observed.

## Variant

`/etc/pulsaros-minimal-build` exists in the image, so this is the minimal Arch variant (package list `ISO/configs/base-arch-minimal.list`).
`/etc/os-release`: "Pulsar OS Bitten Fruit 2.0-preview (Arch Based)".

## Versions (from `/var/lib/pacman/local/*/desc`)

| Package | Version |
|---|---|
| gnome-shell | 1:51.1-1 |
| mutter | 51.1-1 |
| gnome-session | 51.0-1 |
| gjs | 2:1.90.1-1 |
| bluez / bluez-utils | 5.88-1 |
| systemd | 262.2-1 |
| dbus-broker | 37-3 |
| NetworkManager | 1.58.1-3 |
| openssh | 10.6p1-3 |
| sddm | 0.21.0-7 |
| linux | 7.2.15.arch1-1 |

So GNOME Shell 51.1 and BlueZ 5.88.

## Graphical session and systemd user manager

- Display manager is SDDM, not GDM. `/etc/sddm.conf.d/autologin.conf` is `[Autologin] User=live`, `Session=gnome`. `ISO/build-iso.sh` (~line 2079) writes it ("GNOME Wayland").
- `bluetooth.service` is enabled (`bluetooth.target.wants`). `NetworkManager.service` is enabled. `pipewire.service` and `wireplumber.service` user units are shipped.
- The user manager is `user@1000.service`, started by logind when `live` logs in through SDDM's PAM session. `dbus-broker` user units and the `gnome-session*` user units are present in `/usr/lib/systemd/user/`. A GNOME Wayland session therefore runs under a systemd user manager, in the live session and on an installed disk (same image, same units). Not observed live.
- No linger setup was found (no `/var/lib/systemd/linger`). The user manager exists only while `live` has a session.
- The kernel cmdline from `build-iso.sh` (~line 2848) is `archisobasedir=live archisolabel=PULSAR_ISO cow_spacesize=4G ...`; the root is overlaid on the squashfs, so changes in the live session are lost at reboot.

## User, password, autologin

- Live user `live`, uid 1000, shell `/bin/bash`, home `/home/live`, in group `wheel`. `root` also exists.
- Both have yescrypt-hashed passwords in `/etc/shadow`; the plaintext is not documented in the ISO repo (no `chpasswd`/`useradd` for `live` in `build-iso.sh`). The password is not needed: SDDM autologs in, and `/etc/sudoers.d/live` is `live ALL=(ALL) NOPASSWD:ALL`.
- `pulsar-live-nopasswd.service` (source: `pulsaros-essential/etc/systemd/system/`) also installs a polkit rule answering YES to admin actions when the cmdline contains `boot=live|archisobasedir|archisolabel|...`, and removes it on an installed system.
- After install (installer `pulsaros-recovery/usr/share/pulsaros-recovery/recovery.py` copies the image to disk): the cmdline markers are gone, so `pulsar-ootb.service` creates `/etc/pulsar-need-setup` when no non-`live` uid>=1000 user exists, and `pulsaros-live-autologin.service` keeps `User=live` autologin so first boot lands in the Setup Assistant (`welcome_ootb.py`). That assistant runs `useradd`, then `usermod -L -s /usr/sbin/nologin live` (line ~2632); once a real user exists, autologin is removed and `pulsar-cleanup-live.sh` deletes `live`. Sources: `pulsaros-sddm/`, `pulsaros-welcome/`.
- Consequence for tests: a guest booted from the ISO is always user `live` with passwordless sudo; an installed-but-not-yet-set-up guest is also `live`; after setup the user is whatever the assistant created.

## Guest to host reachability

`run-qemu.sh` uses `-nic user,model=virtio-net-pci` with no `hostfwd`, no `-virtfs`, no virtiofs, no virtio-serial/spice agent.

- Outbound network: yes, QEMU user-mode (SLIRP). The guest gets 10.0.2.15 via NetworkManager DHCP; the host is reachable from the guest at 10.0.2.2 (QEMU documented default).
- Host to guest: not with the stock script (no port forward). Needs an added `hostfwd=tcp::2222-:22` on `-nic user`.
- ssh: `openssh` is installed (`sshd`, `sshd.service`), but `sshd.service` is not enabled in the image (no `multi-user.target.wants/sshd.service`). Config is the Arch default plus `UsePAM yes`, `KbdInteractiveAuthentication no`; password auth is on by default, but the `live` password is unknown. Start it by hand (`sudo systemctl start sshd`) and put a key in `~/.ssh/authorized_keys`.
- Shared folder: not configured. The initramfs lists `9p 9pnet 9pnet_virtio virtio_pci virtio_blk` in `MODULES` (`build-iso.sh` ~line 2137), so a `-virtfs ...,mount_tag=X` share can be mounted with `mount -t 9p`, but the script must add the device. No `qemu-guest-agent` or `spice-vdagent` package in the image.
- Alternative with no script change: serve files from the host (`python -m http.server`) and `curl http://10.0.2.2:PORT/...` in the guest; `curl` is in the base list.

## Extensions and `gnome-extensions`

- `/usr/bin/gnome-extensions` exists (part of gnome-shell 51.1, needs gjs 1.90.1; both present).
- System extension dir `/usr/share/gnome-shell/extensions/` holds 20 extensions (appindicatorsupport, blur-my-shell, user-theme, pulsar-dock, pulsaros-global-menu, macos-control-centre-lg, flydrop, and others, all provided by repo packages).
- User dir `~/.local/share/gnome-shell/extensions/` is not pre-created (`/home/live/.local` exists; no `gnome-shell` folder was listed under `/etc/skel`). GNOME Shell scans both dirs; a package installed at `/usr/share/gnome-shell/extensions/<uuid>` is discoverable as a system extension without writing to $HOME.
- `/etc/dconf/db/local.d/00-pulsaros-theme` (plus `locks/00-pulsaros-theme`) is the system dconf profile. If `org.gnome.shell enabled-extensions` is locked there, `gnome-extensions enable` will not persist; check before relying on it in #150. (Lock file contents were not read.)
- `gnome-extensions` talks to the running shell over D-Bus (`org.gnome.Shell.Extensions`), so it must run as `live` inside the graphical session (a terminal in the session, or ssh with `DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus`). Not exercised.

## Not verified (needs a boot)

Actual SLIRP lease, that the user manager and `bluetoothd` come up, that `gnome-extensions list` works, the dconf lock effect, and the `live` password.
Also: QEMU gives the guest no Bluetooth controller by default; testing BlueZ behavior needs a passthrough USB adapter (`-device usb-host`) or a virtual controller, which `run-qemu.sh` does not provide.

## Sources

- `ISO/run-qemu.sh`, `ISO/build-iso.sh`, `ISO/configs/base-arch-minimal.list`
- ISO image files: `/var/lib/pacman/local/*/desc`, `/etc/{passwd,shadow,group,os-release,sddm.conf.d/*,sudoers.d/live,ssh/*}`, `/etc/systemd/system/*.service`
- This repo: `pulsaros-essential`, `pulsaros-sddm`, `pulsaros-welcome`, `pulsaros-recovery`
- QEMU user networking defaults (10.0.2.0/24, host 10.0.2.2): https://wiki.qemu.org/Documentation/Networking
