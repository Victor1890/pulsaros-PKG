# Debian forky build check: pulsaros-control-center

Evidence for issue #123 (spec #120). Date: 2026-11-10. Image: `debian:forky` (gnome-control-center 51.1-2, libadwaita 1.10.0, GTK 4.24.1).

## Commands

Run from the repo root, nothing uploaded or deployed.

```bash
docker run -d --name pcc-forky debian:forky sleep infinity
# base tools the script itself needs before it can run (it installs the rest)
docker exec pcc-forky bash -c 'apt-get update -qq && apt-get install -y -qq --no-install-recommends fakeroot dpkg-dev patch curl ca-certificates git'
# repo copied to /work (without .git, build/), then:
docker exec -w /work pcc-forky ./package-and-deploy.sh pulsaros-control-center --branch forky --no-arch
# install in the same container
docker exec pcc-forky bash -c 'cd /work/build/packages && apt-get install -y ./pulsaros-control-center_*.deb && /usr/bin/gnome-control-center --version'
# stricter check: install in a clean debian:forky with no -dev packages
docker exec pcc-clean bash -c 'apt-get install -y --no-install-recommends /pcc.deb && /usr/bin/gnome-control-center --version'
```

`--no-arch` skips the Arch build (no `makepkg` in the image anyway). The script installs the build dependencies itself when run as root.

## Results

| Step | Result |
|---|---|
| `package-and-deploy.sh pulsaros-control-center --branch forky` | exit 0, `pulsaros-control-center_1.0.44-deb14_amd64.deb` (version is auto-incremented in the container copy) |
| Build tag | 51.1 |
| Patches | all 19 applied in order (0100 to 1900), no fuzz, no rejects |
| Blueprint / Meson / ninja | all `.blp` compiled; meson configured; ninja 776 of 776 steps, including the Printers patch |
| `apt-get install ./x.deb` (build container and clean container) | exit 0, no dependency error |
| `/usr/bin/gnome-control-center --version` | exit 0, prints `gnome-control-center 51.1` (with a `Local options` header line upstream prints) |
| `ldd /usr/bin/gnome-control-center` in clean container | 0 libraries not found |

Not run: starting the app on a display (no GUI in the container), `--deploy`, `--upload`, trixie and `debian:testing` builds (ticket #124).

## What the build exposed and fixed

1. `prepare-assets.sh` build-dependency install failed silently. It listed `libgnome-rr-4-dev` and `libtracker-sparql-3.0-dev`, which are not in forky; apt refuses the whole list on one unknown name and `|| true` hid it, so nothing was installed. GNOME 50+ now has its own list taken from the forky Build-Depends of gnome-control-center 51.1-2, and a failure is fatal. The GNOME 48 list is unchanged.
2. Meson failed with `Dependency "gi-docgen" not found` in the malcontent subproject: forky has libmalcontent 0.13.1 and 51.1 wants >= 0.14.alpha. `prepare-assets.sh` now passes `-D malcontent=false` when the system library is older than 0.14.
3. The `.deb` did not install on forky: `libaccountsservice0` and `libxml2` do not exist there (now `libaccountsservice1`, `libxml2-16`), and the binary needs nine more runtime libraries that nothing pulled in (`libwacom9`, `libibus-1.0-5`, `libgnome-bg-4-2t64`, `libgoa-backend-1.0-2`, `libsmbclient0`, `libgsound0t64`, `libnma-gtk4-0`, `libgnome-bluetooth-ui-3.0-13`, and `libgnome-qr-gtk-4-0`). `DEBIAN/control` Depends lists them with trixie-compatible alternatives where the name differs; `libgnome-qr-gtk-4-0` is forky only, so `prepare-assets.sh` appends it to the staged control for GNOME 50+. Version 1.0.42 to 1.0.43.

## Skipped or reduced

- No patch was skipped or changed.
- Malcontent is off on forky: no parental-controls integration (Wellbeing/Screen Time settings sync with malcontent, Users panel parental controls). Debian's own package keeps malcontent 0.13 by relaxing the version check and reverting the Wellbeing sync; this build drops malcontent instead (smaller change, same loss of the sync).
- Minimum versions are not enforced in Depends (`libgtk-4-1 (>= 4.23)`, `libadwaita-1-0 (>= 1.8)`): forky satisfies them, and a versioned Depends would break the trixie build that shares this control file.
