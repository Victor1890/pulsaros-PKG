# QEMU USB passthrough of the Realtek Bluetooth adapter (0bda:4852)

Answers issue #148. Research only: no host state was changed and no QEMU passthrough was run.

## Host facts (read-only inspection)

- Adapter: `0bda:4852` Realtek Bluetooth Radio, sysfs `1-3`, `/dev/bus/usb/001/003`.
- Node mode: `root:root 0664`. The user is in `kvm` but not `root`, so the node is read-only to the user and libusb cannot open it read-write.
- Both interfaces (`1-3:1.0`, `1-3:1.1`) are bound to `btusb`.
- Versions: qemu-system-x86 11.1.2, bluez 5.87, linux-firmware-realtek 20260916, kernel 7.2.15.
- Host firmware present: `/usr/lib/firmware/rtl_bt/rtl8852cu_fw.bin.zst`, `rtl8852cu_fw_v2.bin.zst`, `rtl8852cu_config.bin.zst`.
- `/usr/lib/udev/rules.d/70-uaccess.rules` exists, so `TAG+="uaccess"` rules are honoured on this host.

## 1. QEMU arguments

Source: QEMU docs, "USB emulation" (https://www.qemu.org/docs/master/system/devices/usb.html).

- `usb-host` matches by `vendorid`+`productid` (any port), `hostbus`+`hostport` (physical port, stable), or `hostbus`+`hostaddr` (ad hoc; the address changes on replug).
- Suggested for this adapter:

  ```
  -device qemu-xhci,id=xhci \
  -device usb-host,bus=xhci.0,vendorid=0x0bda,productid=0x4852
  ```

  `hostbus=1,hostport=3` is sturdier if another 0bda:4852 could appear. `hostaddr=3` is not stable across replugs.
- Runtime: monitor `info usbhost`, then `device_add usb-host,vendorid=0x0bda,productid=0x4852`.
- The docs' own passthrough example uses EHCI. They describe XHCI (`qemu-xhci`) as supporting USB 1.1/2.0/3.0 devices but show no XHCI passthrough line. The line above is composed from those two parts, not copied from the docs.
- Reset policy property: `guest-reset` / `guest-resets-all`. Default is `guest-reset=true,guest-resets-all=false` (guest may reset only before the device has a bus address). `guest-reset=false` forbids guest-initiated resets of the physical device.
- Docs caveats: "experimental"; no hubs; after relaunching QEMU you may need to replug the device (documented bug).

## 2. Permissions for a non-root user

- The QEMU docs only say: "Only root can access USB devices directly. Run QEMU as root, or change permissions on the devices you need" (their `/proc/bus/usb` advice is obsolete).
- libusb opens the usbfs node (`/dev/bus/usb/BBB/DDD`) read-write; the node is root:root 0664, so a rule is required.
- Narrow udev rule (keys per udev(7): `SUBSYSTEM`, `ENV{DEVTYPE}`, `ATTRS`, `GROUP`, `MODE`), e.g. `/etc/udev/rules.d/99-qemu-bt-passthrough.rules`:

  ```
  SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="4852", GROUP="kvm", MODE="0660"
  ```

  `GROUP="kvm"` reuses a group the user already has. `TAG+="uaccess"` (ACL for the active-seat user) is the alternative; udev(7) does not define `uaccess`, so that behaviour comes from systemd's `70-uaccess.rules` and was not verified against its docs.
- Not applied on this host (research only). Reload would be `udevadm control --reload && udevadm trigger -s usb -c add`, then replug.

## 3. Detaching `btusb` and BlueZ, and getting them back

Sources: QEMU `hw/usb/host-libusb.c`; libusb API docs; kernel USB API docs.

- QEMU detaches by itself. `usb_host_open()` calls `usb_host_detach_kernel()`, which runs `libusb_detach_kernel_driver()` on each interface with an active driver and records `detached`. Interfaces are claimed when the guest sets a configuration (`usb_host_claim_interfaces()`). QEMU does not use `libusb_set_auto_detach_kernel_driver`.
- On close (guest shutdown, QEMU exit, device_del, open errors) `usb_host_close()` releases interfaces, calls `libusb_reset_device()`, then `usb_host_attach_kernel()` (`libusb_attach_kernel_driver()`), then closes. `usb_host_exit_notifier()` does the same at QEMU exit. So `btusb` rebinds without manual sysfs `unbind`/`bind` on a normal exit.
- libusb: attach returns `LIBUSB_ERROR_BUSY` if the interface is claimed elsewhere. `libusb_reset_device()` can make the device look disconnected/reconnected (`LIBUSB_ERROR_NOT_FOUND`).
- Kernel: `usb_reset_device()` notifies bound drivers via `pre_reset`/`post_reset`; drivers without them are unbound and rebound.
- Auto mode (vendorid/productid, no fixed address): `usb_host_auto_check()` polls every 2000 ms while the VM runs, so QEMU grabs the device once the VM is running and re-acquires it after replug. After three open failures it stops retrying silently.
- BlueZ (inference, not verified in a BlueZ primary doc): when `btusb` unbinds, `hci0` is removed and `bluetoothd` sees the controller disappear; on rebind a new `hci0` appears and bluetoothd re-registers it. Expect host Bluetooth (paired devices, audio) to drop while the VM runs. Stopping `bluetooth.service` first is optional; restart it after QEMU exits. Confirm on a throwaway run before relying on it.
- If QEMU is SIGKILLed or crashes, close/reattach may not run. Recover by replugging, or as root `echo 1-3:1.0 > /sys/bus/usb/drivers/btusb/bind` (and `1-3:1.1`), or `modprobe -r btusb && modprobe btusb`. Standard driver-core behaviour; not quoted from a doc here.

## 4. Realtek firmware in the guest

- Realtek chips load firmware at runtime through kernel `btrtl`. For lmp_subver 0x8852, hci_rev 0x000c, `btrtl.c` tries `rtl_bt/rtl8852cu_fw_v2.bin`, then `rtl_bt/rtl8852cu_fw.bin`, plus optional `rtl_bt/rtl8852cu_config.bin`, via `request_firmware()`. These files exist on the host, so the adapter very likely belongs to the 8852C family. `btrtl.c` matches on LMP/HCI revision, not USB ID, so the chip was not confirmed from the device itself.
- The guest therefore needs `btusb` + `btrtl` and `linux-firmware-realtek` (or the `rtl_bt/*` files). Add that package to the guest image for this use.
- Inference: Realtek firmware lives in controller RAM, so a controller the host already initialised may already hold firmware when the guest sees it; the guest's `btrtl` may skip or redo the download. Not verified.
- Not verified: the `0bda:4852` entry in `btusb.c`'s `usb_device_id` table (kernel.org and GitHub fetches failed). The host already binds `btusb` to it, so the host kernel supports it.

## 5. Known failure modes

- Permission denied on open: QEMU reports `failed to open host usb device ...`; libusb permission errors surface as `ACCESS` through `usb_host_libusb_error()`. Fix with the udev rule.
- Guest reset: with `guest-reset=true`, a reset before addressing triggers `libusb_reset_device()`; if it fails QEMU calls `usb_host_nodev()` and closes the device. Re-enumeration after reset can invalidate the handle (libusb). Mitigation: `guest-reset=false`.
- Disconnects: `LIBUSB_TRANSFER_NO_DEVICE` / `LIBUSB_ERROR_NO_DEVICE` closes the device (`usb_host_nodev()` then `usb_host_close()`); auto mode may re-grab it.
- Relaunch needing replug: listed as a known bug in the QEMU docs.
- Claim mismatch: if the claimed interface count differs from `bNumInterfaces`, the guest's set-configuration gets a STALL. Both interfaces (`1.0`, `1.1`) must be free of other claimants.
- The "no hubs" warning does not apply: the adapter is a device on a root hub port, not a hub.
- Host suspend while passed through is untested.

## Recommended recipe (untested)

1. Add the udev rule (`GROUP="kvm"`), reload, replug.
2. Optionally `systemctl stop bluetooth`.
3. Launch with `-device qemu-xhci,id=xhci -device usb-host,bus=xhci.0,vendorid=0x0bda,productid=0x4852,guest-reset=false`.
4. Guest image: kernel with `btusb`/`btrtl`, `linux-firmware-realtek`, BlueZ.
5. After QEMU exits, confirm `readlink /sys/bus/usb/devices/1-3:1.0/driver` ends in `btusb`, then start `bluetooth` again.

## Gaps

- Arch Wiki (QEMU, Bluetooth) fetches were blocked by bot protection; nothing here comes from it.
- BlueZ behaviour on controller removal is inferred, not sourced.
- The btusb device-table entry for 0bda:4852 was not read.
- Nothing was run against the hardware.

## Sources

- https://www.qemu.org/docs/master/system/devices/usb.html
- https://gitlab.com/qemu-project/qemu/-/raw/master/hw/usb/host-libusb.c
- https://libusb.sourceforge.io/api-1.0/group__libusb__dev.html
- https://www.kernel.org/doc/html/latest/driver-api/usb/usb.html
- https://www.kernel.org/doc/html/latest/driver-api/usb/persist.html
- https://raw.githubusercontent.com/torvalds/linux/master/drivers/bluetooth/btrtl.c
- https://man7.org/linux/man-pages/man7/udev.7.html
