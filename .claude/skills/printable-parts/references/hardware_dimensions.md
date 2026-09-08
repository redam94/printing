# Hardware dimensions reference

All mm. **Verified** = read from the cited primary document. **UNVERIFIED** = secondary
source or inferred; measure before trusting. `lib/fasteners/hardware.py` and
`lib/patterns/*` encode these numbers — change both together.

Contents: 1 Raspberry Pi 4/5 · 2 Pi Zero · 3 ESP32 boards · 4 Metric fasteners ·
5 Heat-set inserts · 6 VESA / DIN rail · 7 Fans · 8 Misc (USB-C, SD, 18650, JST)

## 1. Raspberry Pi 4 Model B / Pi 5

Origin at the board corner where the microSD edge (left) meets the USB-C/HDMI edge (bottom).
GPIO along the top edge; USB-A/Ethernet on the right edge. Library convention differs:
`lib.patterns.pi` puts the origin at the **hole-pattern centre**, +X toward USB/Ethernet.

| Item | Value | Status |
|---|---|---|
| Board outline | 85 x 56, corner R3.0 | Verified (R3 labelled on Pi 4 drawing only) |
| Hole pattern | 58 (X) x 49 (Y); centres (3.5, 3.5) (61.5, 3.5) (3.5, 52.5) (61.5, 52.5) | Verified |
| Hole diameter | Ø2.7 (M2.5) | Verified |
| GPIO 2x20 header | top edge, centre x = 32.5 | Verified |
| 40-way IDC socket on the header (ribbon window) | 58 wide, 8-19 mm above PCB top incl. strain relief; bare ribbon 52 wide at 15-18 | UNVERIFIED — generic 2x20 IDC data |
| PCB thickness | ~1.6 | UNVERIFIED (not on drawings) |
| Pi 5 Active Cooler pin holes | Ø3 at (61.5, 9.5) and (61.5, 46.5) | Verified Ø and 6 mm offset from M2.5 holes |
| Pi 5 USB-C | centre x = 11.2, bottom edge | Verified |
| Pi 5 micro-HDMI 0 / 1 | centres x = 25.8 / 39.2, bottom edge | Verified |
| Pi 5 Ethernet | centre y = 10.2, right edge (swapped vs Pi 4) | Verified |
| Pi 5 USB-A stacks | centres y = 29.1 and 47.0, right edge | Verified |
| Pi 5 PCIe FPC, fan header, power button, CSI/DSI | not dimensioned on the official drawing | UNVERIFIED — use STEP or measure |
| Pi 4 USB-C / micro-HDMI 0 / 1 | x = 11.2 / 26.0 / 39.5, heights 3.2 / 3.0 | Verified |
| Pi 4 Ethernet | y = 45.75 right edge, height 13.5 | Verified |
| Pi 4 USB-A stacks | y = 27 and 9, height 16.0 (tallest component) | Verified |
| Pi 4 3.5 mm jack / GPIO / SoC / FPC | heights 6.0 / 8.5 / 2.4 / 5.5 | Verified |
| Pi 5 component heights | assume Pi 4-like: USB-A ~16 tall | UNVERIFIED |
| Active Cooler | heatsink 63.5 x 42.5, 30 mm fan, 13.7 tall above PCB | Verified |

Enclosure rule of thumb (Pi 4/5): inner cavity ≥ 88 x 59, lid clearance ≥ 20 above PCB top
without cooler, ≥ 24 with the Active Cooler (leave ≥ 10 mm of air above the fan). If the lid
screws into corner bosses (Ø7.2 for M3 inserts), the cavity needs ≥ 5.6 mm between the board edge
and the wall on every side — the Ethernet jack sits 2.2 mm from the USB-C-edge corner.

Pi 5 connector envelopes used by `patterns.pi5_port_cutouts` (heights relative to PCB top; the
plug envelope is what a cable overmold needs when the wall stands a few mm off the board edge):

| Port | Centre (lib coords) | Body W x H | Plug envelope W x [z0, z1] | Status |
|---|---|---|---|---|
| USB-C | x = −21.3, −Y edge | 9.0 x 3.2 | 13.0 x [−1.9, 5.1] | position Verified; body Pi 4; plug UNVERIFIED |
| micro-HDMI 0 / 1 | x = −6.7 / +6.7, −Y edge | 7.6 x 3.0 | 10.0 x [−1.5, 4.5] | position Verified; body/plug UNVERIFIED |
| Ethernet | y = −17.8, +X edge | 16.0 x 13.5 | = body | position Verified; body Pi 4 |
| USB-A stacks | y = +1.1 / +19.0, +X edge | 13.3 x 15.6 | = body | position Verified; body generic dual USB-A |
| microSD window | y = 0, −X edge | 12.0 x [−3.6, 0] | 16.0 x [−3.6, 0] | UNVERIFIED (slot assumed centred, card under PCB) |

Component default adds 0.75 mm clearance per side. Webs between adjacent windows end up 1.6–3 mm.

Sources: https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-mechanical-drawing.pdf ·
https://datasheets.raspberrypi.com/rpi5/raspberry-pi-5-mechanical-drawing.pdf ·
https://datasheets.raspberrypi.com/cooling/raspberry-pi-active-cooler-mechanical-drawing.pdf

## 2. Raspberry Pi Zero / Zero W / Zero 2 W

| Item | Value | Status |
|---|---|---|
| Board outline | 65 x 30, corner R3.0 | Verified |
| Hole pattern | 58 x 23, holes 3.5 from every edge | Verified |
| Hole diameter | Ø2.75 ±0.05 (M2.5) | Verified (Zero v1.2 drawing) |
| GPIO 2x20 | top edge, centre x = 32.5 | Verified |
| mini-HDMI / micro-USB data / micro-USB power | bottom edge, centres x = 12.4 / 41.4 / 54.0 | Verified |
| CSI camera FPC | right edge, centred | UNVERIFIED |

Sources: https://datasheets.raspberrypi.com/rpizero/raspberry-pi-zero-mechanical-drawing.pdf ·
https://datasheets.raspberrypi.com/rpizero2/raspberry-pi-zero-2-w-mechanical-drawing.pdf

## 3. ESP32 development boards (no mounting holes on any of these)

| Board | PCB L x W | Pins | Row spacing | USB | Status |
|---|---|---|---|---|---|
| ESP32-DevKitC V4 | 48.26 x 27.94 PCB, antenna overhang 6.04 → 54.3 overall | 2x19 @ 2.54 | 25.40 | micro-USB, short edge opposite antenna | Verified |
| ESP32-S3-DevKitC-1 v1.1 | 62.74 x 25.40 | 2x22 @ 2.54 | 22.86 (rows 1.27 from edges) | 2x micro-USB, connector zone 8.0 past last pin row | Verified |
| ESP32-WROOM-32 module | 18.0 x 25.5 x 3.1 | — | — | — | Verified |
| NodeMCU-32S | 48.26 x 25.4 | 2x19 | 22.86 | micro-USB | Secondary |
| DOIT DevKit V1 (30 pin) | 51.8 x 28.2 (sources conflict: 23.37 also quoted) | 2x15 | ? | micro-USB | UNVERIFIED — measure |
| ESP32-C3 SuperMini | 22.5 x 18 | 16 | — | USB-C | Secondary |

Mounting without holes: edge slots (slot = PCB 1.6 + 0.2–0.3, see `primitives.pcb_slot_cradle`),
header-pin combs at the row spacing above, corner snap tabs, or a strap channel. Keep the
antenna overhang (6.04 on DevKitC) outside metal and clear of thick plastic.

Sources: https://dl.espressif.com/dl/schematics/esp32_devkitc_v4_dimensions.pdf ·
https://dl.espressif.com/dl/schematics/esp_idf/DXF_ESP32-S3-DevKitC-1_V1.1_20220429.pdf ·
https://documentation.espressif.com/esp32-wroom-32_datasheet_en.pdf

## 4. Metric fasteners

Heads (max), ISO 4762 socket / ISO 7380-1 button / ISO 7045 pan / ISO 10642 countersunk:

| Thread | Pitch | Socket dk / k | Button dk / k | Pan dk / k | Csk dk / k | Hex key |
|---|---|---|---|---|---|---|
| M2 | 0.4 | 3.80 / 2.00 | (not ISO) | 3.7 / 1.72 | — | 1.5 |
| M2.5 | 0.45 | 4.50 / 2.50 | (not ISO) | 4.7 / 2.12 | — | 2.0 |
| M3 | 0.5 | 5.50 / 3.00 | 5.70 / 1.65 | 5.7 / 2.52 | 6.0 / 1.7 | 2.5 |
| M4 | 0.7 | 7.00 / 4.00 | 7.60 / 2.20 | 7.64 / 3.25 | 8.0 / 2.3 | 3.0 |

Counterbore: dk + 0.5–1.0, depth ≥ k.

Nuts ISO 4032 (DIN 934 identical for M2–M4) and washers ISO 7089:

| Thread | AF s (max) | AC e (min) | thickness m (max) | washer OD | washer t |
|---|---|---|---|---|---|
| M2 | 4.00 | 4.32 | 1.60 | 5.0 | 0.35 |
| M2.5 | 5.00 | 5.45 | 2.00 | 6.0 | 0.55 |
| M3 | 5.50 | 6.01 | 2.40 | 7.0 | 0.55 |
| M4 | 7.00 | 7.66 | 3.20 | 9.0 | 0.90 |

Nut trap: AF + 0.2–0.3 (M3 → 5.7–5.8), depth m + 0.2, 0.5 x 45° lead-in.

Clearance ISO 273 and pilots:

| Thread | Fine | Medium (default) | Coarse | Tap drill (metal) | Pilot into printed plastic (d − 0.3) |
|---|---|---|---|---|---|
| M2 | 2.2 | 2.4 | 2.6 | 1.6 | 1.7 |
| M2.5 | 2.7 | 2.9 | 3.1 | 2.05 | 2.2 |
| M3 | 3.2 | 3.4 | 3.6 | 2.5 | 2.7 |
| M4 | 4.3 | 4.5 | 4.8 | 3.3 | 3.7 |

FDM prints holes small: add 0.1–0.2 to "medium" (the components' `print_oversize` default is 0.2).
Thread-forming: wall around the hole ≥ screw diameter, depth ≥ 2d; use the tap-drill size for a
tighter, less reusable fit.

Sources: https://www.fasteners.eu/standards/iso/4762/ · .../iso/7380/ · .../ISO/7045/ ·
.../iso/10642/ · .../iso/4032/ · .../iso/7089/ · https://engineeringhardware.com/fastener/clearance-hole-sizes/ ·
https://www.hubs.com/knowledge-base/how-assemble-3d-printed-parts-threaded-fasteners/

## 5. Brass heat-set inserts (CNC Kitchen TC-series; Ruthex RX-M3x5.7 identical)

| Thread | Length | Insert OD | Hole Ø | Min wall | Min boss OD |
|---|---|---|---|---|---|
| M2 | 3.0 | 3.6 | 3.2 | 1.6 | 6.4 |
| M2.5 | 4.0 | 4.6 | 4.0 | 1.6 | 7.2 |
| M3 short | 3.0 | 4.6 | 4.0 | 1.6 | 7.2 |
| M3 standard | 5.7 | 4.6 | 4.0 | 1.6 | 7.2 |
| M3 (Voron 5x4) | 4.0 | 5.0 | 4.4 | 1.6 | 7.6 |
| M4 short / standard | 4.0 / 8.1 | 6.3 | 5.6 | 2.0 | 9.6 |
| M5 short / standard | 5.8 / 9.5 | 7.1 | 6.4 | 2.0 | 10.4 |
| M6 | 6.8 / 12.7 | 8.7 | 8.0 | 2.0 | 12.0 |

Pocket depth = insert length + 0.5–1.0 (melt relief), blind floor ≥ 1.0. Size the pocket per the
insert, never per the screw. McMaster 94180A (tapered) hole sizes UNVERIFIED — use the vendor sheet.

Sources: https://cnckitchen.store/products/heat-set-insert-m3-x-5-7-100-pieces ·
https://kb-3d.com/store/inserts-fasteners-adhesives/927-cnckitchen-lead-cadmium-free-heat-set-inserts-multiple-sizes-metric.html ·
https://www.ruthex.de/en/products/ruthex-gewindeeinsatz-m3-100-stuck-rx-m3x5-7-messing-gewindebuchsen

## 6. VESA FDMI and DIN rail

| VESA variant | Pattern | Screw | Max thread depth into display |
|---|---|---|---|
| MIS-B | 20 x 50 | M4 | 4.0 |
| MIS-C | 35 x 75 | M4 | 5.4 |
| MIS-D 75 / 100 | 75 x 75 / 100 x 100 | M4 | 7.4 |
| MIS-E | 200 x 100 | M4 | 7.4 |
| MIS-F | 200 x 200 (+200 steps) | M6 / M8 | 9–16 |

DIN rail TS35 / TH35 (EN 60715): width 35 (±0.3), depth 7.5 standard or 15 deep, sheet 1.0
(1.0–1.5), perforation slots 15 x 6.2 at 25 pitch. Clip slot 35.3–35.5 wide with a 1.2–1.5 lip pocket
(UNVERIFIED guidance). `patterns.din_rail_ts35_profile` is unvalidated; test-print a clip first.

Sources: https://en.wikipedia.org/wiki/VESA_mount · Phoenix Contact NS 35/7,5 datasheet
https://datasheet.octopart.com/1207650-Phoenix-Contact-datasheet-128607810.pdf

## 7. Axial fans (4 holes on a square)

| Fan | Hole pitch | Hole Ø in frame | Status |
|---|---|---|---|
| 25 | 20 | ~2.8–3.0 (M2.5) | UNVERIFIED |
| 30 | 24.0 ±0.3 | 3.2 | Verified (Delta ASB0312MA-D) |
| 40 | 32.0 | 3.5 (3.2–3.5) | Verified (Arctic) |
| 50 | 40 | — | Secondary |
| 60 | 50.0 | 4.3 | Verified (Delta EFB0612HA) |
| 70 | 60 | — | Secondary |
| 80 | 71.5 | 4.5 | Verified (Delta AFB0812SH) |
| 92 | 82.5 | 4.3–4.5 | Secondary |
| 120 | 105.0 | 4.3 | Verified (Arctic P12) |
| 140 | 124.5 | 4.3 | Secondary |

30/40 mm fans: M3 (or #4 self-tappers). 60 mm+: #6-32 fan screws or M4 with 4.3–4.5 clearance.
Airflow opening ≈ frame − 2 (e.g. 38.2 for 40 mm, 116 for 120 mm).

Sources: https://www.delta-fan.com/Download/Spec/ASB0312MA-D.pdf ·
https://support.arctic.de/products/fan-grill/techdocs/40mm%20Fan%20-%20Mounting%20Hole%20Pattern.pdf ·
https://support.arctic.de/products/p12/techdocs/120mm_fan-Mounting_hole_pattern.pdf

## 8. Miscellaneous

| Item | Value | Status |
|---|---|---|
| USB-C receptacle shell | 8.95 wide x 3.2 high, 9.17 long; opening 8.34 x 2.56 | Verified (GCT USB4085) |
| USB-C panel cutout | 9.5–10 x 3.8–4.0 for the receptacle; ~13 x 7 if the plug overmold must pass | Guidance |
| micro-USB (B) plug | 6.85 x 1.80; overmold max 10.6 x 8.5 | Verified |
| mini-HDMI / micro-HDMI opening | ~10.42 x 2.42 / ~6.4 x 2.8 | UNVERIFIED |
| microSD / SD card | 15 x 11 x 1.0 / 32 x 24 x 2.1 | Verified |
| 18650 cell | Ø18.4 max x 65.0 max; holder envelope Ø18.6–18.8 x 65.5–66 (protected cells to Ø19 x 70) | Verified / guidance |
| 0.1" pin header | 2.54 pitch, 0.64 sq pins | Verified |
| JST XH | 2.5 pitch, 9.8 assembled height | Verified |

Sources: https://gct.co/connector/usb4085 · https://en.wikipedia.org/wiki/USB_hardware ·
https://www.jst-mfg.com/product/pdf/eng/eXH.pdf · https://en.wikipedia.org/wiki/18650_battery
