# Non-ANC AirPods 4: what do the daemon and extension show?

Answers issue #146. Sources are the code on `origin/feat/pulsaros-airpods-implementation`
at `a35c7e01` (`pulsaros-airpods/` is not on `main` yet). Nothing was run on hardware; this is
a read of the code and fixtures.

## Answer

A non-ANC AirPods 4 is handled correctly. Every control that needs ANC or an H2 chip is hidden,
and only battery rows and the Ear detection submenu remain. Four rough edges are listed under
"Findings".

## Which model id it gets

- The model number comes from the AAP metadata packet (`main.cpp` `parseModelNumber(...)`, line ~1085).
  `enums.h` maps `A3053`, `A3050`, `A3054` to `AirPodsModel::AirPods4` (enum value 9) and
  `A3056`, `A3055`, `A3057` to `AirPods4ANC` (value 10).
- The BLE advertisement path also sets it: `ble/blemanager.cpp` maps `0x1920` to `AirPods4` and
  `0x1B20` to `AirPods4ANC`. `bleDeviceFound` (`main.cpp` ~1495) ignores an `Unknown` result,
  so it never clobbers a model learned from AAP.
- The raw `A<NNNN>` code is persisted and re-parsed on the next start (`deviceinfo.hpp` `loadFromSettings`).

## What lands in status.json

Built by `statusJson()` in `main.cpp` (~1700-1770). For a connected non-ANC AirPods 4:

| Key | Value | Why |
|---|---|---|
| `model_name` | `"AirPods 4"` | `modelDisplayName`; deliberately identical to the ANC model |
| `model_int` | `9` | `AirPods4` (ANC is `10`) |
| `model_number` | `"A3053"` etc. | raw AAP code |
| `is_pro_series` | `false` | |
| `is_headset` | `false` | |
| `supports_noise_control` | `false` | `supportsNoiseControl`: only the ANC/Pro/Max cases return true |
| `supports_noise_off` | `true` | `model != AirPodsPro3`; meaningless when noise control is false |
| `supports_adaptive` | `false` | `hasH2ListeningFeatures` covers only AirPods4ANC, Pro 2, Pro 3, Max 2 |
| `supports_conversational_awareness` | `false` | same helper |
| `supports_one_bud_anc` | `false` | `supportsOneBudANC` lists AirPods4ANC, Pro 1-3 only |
| `noise_mode` | `2` (stale default) | see finding 1 |
| `left`, `right`, `case` | present once a battery packet arrives | |
| `ear_detection_behavior` | `0` to `2` | |

## Which popover controls appear

`model.js` `parseStatus` reads the `supports_*` keys; `indicator.js` `_syncControls` applies them.

| Control | Shown? | Reason |
|---|---|---|
| Title and subtitle ("AirPods 4" / device name) | yes | `modelName`, `deviceName` |
| Left, right, case battery rows | yes | not a headset |
| Listening-mode segmented row | hidden | `availableModes` returns `[]` when `supportsNoiseControl` is false |
| Adaptive noise-level slider | hidden | needs `supportsAdaptive && noiseMode === 3` |
| Conversation Awareness switch | hidden | `supportsConversationalAwareness` false |
| One-Bud ANC switch | hidden | `supportsOneBudAnc` false |
| Ear detection submenu | shown | `!isHeadset`; AirPods 4 has in-ear detection |
| Separator | shown | because the Ear detection submenu is shown |

No control is wrongly shown or hidden for a correctly identified device. The tests cover the
"no modes" case with a synthetic AirPods 3 (`tests/model_check.js` lines 80-83), and the four
fixtures (`airpods4-anc`, `pro3`, `max2`, `in-case`) have no plain AirPods 4 file.

## Findings

1. **Stale `noise_mode`.** `DeviceInfo::m_noiseControlMode` defaults to `Transparency` (2) and a
   non-ANC AirPods 4 never sends a noise-control packet, so `status.json` reports `noise_mode: 2`.
   The extension ignores it because no mode row is built, so nothing visible is wrong. Any other
   consumer of `status.json` would read a mode the device does not have. `reset()` sets it to `Off` (0).
2. **Fail-open on `Unknown`.** `supportsNoiseControl(Unknown)` is true by design. If a non-ANC
   AirPods 4 is not yet identified (first pairing before the AAP metadata or a valid-IRK BLE
   advertisement, or a model number missing from the map), the popover shows Off, Noise
   Cancellation and Transparency buttons that do nothing. They correct themselves once the model
   resolves. The extension has the same fallback for absent keys (`capability(raw, 'supports_noise_control', true)`),
   which only matters with an older daemon.
3. **Noise verbs are not gated by model.** `setNoiseControlMode`, `cycleNoiseControlMode` and the
   `noise:*` IPC verbs (`main.cpp` 372-391, 438-447, 2083-2091) never check `supportsNoiseControl`.
   The popover cannot reach them for this model, but `librepods-ctl noise:anc` or the tray
   middle-click would send an ANC packet that the earbuds presumably ignore. Unverified on hardware.
4. **Same display name for both models.** Both variants show "AirPods 4" (`enums.h` comment says
   this is intentional). The panel cannot tell a user which one it detected, apart from the
   hidden controls. `model_int` and `model_number` are the only distinguishing fields.

## Unverified

- That the plain AirPods 4 lacks Adaptive Audio and Conversation Awareness is taken from the
  `enums.h` comments citing Apple's compare page; I did not re-fetch that page.
- Behaviour on real hardware (finding 3, and whether `0x1920` is the BLE id a real unit sends).

## Suggested follow-ups

- Add a `tests/fixtures/airpods4.json` (plain AirPods 4) and a matching `model_check.js` case.
- Report `noise_mode: -1` when `supports_noise_control` is false (finding 1).
- Gate the noise verbs on `supportsNoiseControl(model)` in the daemon (finding 3).
