# omen-rgb-linux

A standalone, reverse-engineered Linux driver and CLI utility to control 4-zone RGB keyboard lighting on HP OMEN laptops via direct ACPI WMI kernel calls (`\_SB.WMID.WMAA`).

---

## Features
- **Direct Kernel ACPI Communication:** Bypasses proprietary userland software, writing directly to the embedded controller via `/proc/acpi/call`.
- **Independent 4-Zone Control:** Granular control over the **WASD**, **Left**, **Center**, and **Right** zones.
- **Native Hardware Dimming:** Utilizes CommandType 5 calls for hardware brightness without modifying the active RGB palette.
- **Unprivileged Access:** Includes `systemd-tmpfiles` rules to grant write access to `/proc/acpi/call` without requiring `sudo`.
- **Boot & Sleep Persistence:** Ships with a `systemd-sleep` hook to re-latch lighting states automatically upon waking from S3/S2idle suspend.
- **Optional Frontends:** Supports third-party GUIs like OpenRGB via a dedicated sACN bridge (see [docs/OPENRGB.md](docs/OPENRGB.md)).

## Tested Hardware
- **HP OMEN 16 / Transcend** (Intel Core Ultra / AMD Ryzen + NVIDIA RTX GPUs)
- **Ubuntu 24.04 / 26.04 LTS** (Kernel 6.x / 7.x)

---

## Installation

### 1. Clone & Run Installer
```bash
git clone https://github.com/kishanmokaria/omen-rgb-linux.git
cd omen-rgb-linux
chmod +x install.sh
./install.sh
```

> **Note on Secure Boot:**  
> If Secure Boot is active, compiling `acpi-call-dkms` requires enrolling a Machine Owner Key (MOK). If prompted, enter a temporary password, reboot, select **Enroll MOK** on the blue screen, and enter that password.

---

## CLI Driver Usage

### Set Discrete Zone Colors (Hex)
```bash
omen-rgb set --wasd FF0000 --left 00FF00 --center 0000FF --right FFFFFF
```

### Set Static Color (All Zones)
```bash
omen-rgb static 00E5FF
```

### Hardware Brightness & Power State
```bash
omen-rgb brightness 100   # Range: 0 to 255 (hardware dimming)
omen-rgb off              # Disables keyboard LEDs (preserves colors in memory)
omen-rgb on               # Restores backlight to previous state
```

---

## ACPI WMI Protocol Specification

Lighting is controlled through the ACPI method `\_SB.WMID.WMAA`, which calls the internal BIOS dispatcher `HWMC`.

### 1. Command Buffer Structure
Every hardware command requires a 144-byte buffer (16-byte header + 128-byte EC data payload):

```text
Byte Offset | Length   | Value      | Description
------------|----------|------------|----------------------------------------------
00 - 03     | 4 bytes  | 0x53454355 | Signature: "SECU"
04 - 07     | 4 bytes  | 0x00020009 | Command ID: 0x20009 (Decimal 131081)
08 - 11     | 4 bytes  | 0x00000003 | Command Type: 3 (Set Color), 5 (Brightness)
12 - 15     | 4 bytes  | 0x00000080 | Payload Size: 128 bytes (0x80)
16 - 143    | 128 byte | [Data...]  | EC Command Parameters & Color Array
```

### 2. Payload Zone Mapping (Command Type 3)
Colors are structured in raw `[R, G, B]` triplets. The hardware registers zones starting at payload byte 25 (absolute call buffer index 41):

```text
Hardware Zone | EC ID | Payload Slice (Index in Payload) | Absolute Buffer Offset
--------------|-------|----------------------------------|-----------------------
Right         | 0     | payload[25:28]                   | 41 - 43
Center        | 1     | payload[28:31]                   | 44 - 46
Left          | 2     | payload[31:34]                   | 47 - 49
WASD          | 3     | payload[34:37]                   | 50 - 52
```

Writing this structured buffer to `/proc/acpi/call` triggers an immediate embedded controller interrupt that re-latches the keyboard PWM lines.

---

## Power Management & Suspend Persistence

The Linux kernel resets EC registers upon entering ACPI state S3 / S2idle. The driver ships with a sleep hook located at `/usr/lib/systemd/system-sleep/omen-rgb-resume.sh` that detects `post` resume events and re-latches the active lighting profile.

---

## OpenRGB Bridge
For graphical control and animated effects using OpenRGB, see [docs/OPENRGB.md](docs/OPENRGB.md).

---

## License
MIT
