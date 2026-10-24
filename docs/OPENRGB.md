# OpenRGB Integration Guide

This document explains how to connect OpenRGB and the OpenRGB Effects Plugin to the HP OMEN 4-Zone keyboard driver via the bundled E1.31 sACN UDP bridge.

---

## Architecture

```text
OpenRGB + Effects Plugin (Flatpak)
       │
       ▼  (E1.31 sACN UDP packets on localhost:5568)
omen-rgb-bridge (Daemon listening at byte offset 125)
       │
       ▼
/proc/acpi/call  ──▶  \_SB.WMID.WMAA (131081)
       │
       ▼
Hardware Keyboard LEDs (WASD, Left, Center, Right)
```

### Why E1.31 sACN over the OpenRGB SDK?
- **Zero Plugin Crashes:** Bypasses `openrgb-python` client crashes caused by unhandled plugin protocol headers (`StopIteration`) and broken socket magic handshakes.
- **Zero Latency:** Pure event-driven UDP streaming. No polling or blocking `.update()` calls.
- **Calibrated Framing:** Stream channel 1 starts at byte index `125` in the sACN DMP frame.

---

## Setup Instructions

### 1. Enable the Bridge Daemon
```bash
mkdir -p ~/.config/systemd/user
cp systemd/omen-rgb-bridge.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now omen-rgb-bridge.service
```

### 2. Configure OpenRGB Virtual Zones
Close OpenRGB completely:
```bash
flatpak kill org.openrgb.OpenRGB 2>/dev/null || true
```

Open `~/.var/app/org.openrgb.OpenRGB/config/OpenRGB/OpenRGB.json` and replace the `E131Devices` section with the 4 discrete zones:

```json
    "E131Devices": {
        "devices": [
            {
                "ip": "127.0.0.1",
                "name": "WASD",
                "num_leds": 1,
                "rgb_order": 0,
                "start_channel": 0,
                "start_universe": 1,
                "type": 0
            },
            {
                "ip": "127.0.0.1",
                "name": "Left",
                "num_leds": 1,
                "rgb_order": 0,
                "start_channel": 3,
                "start_universe": 1,
                "type": 0
            },
            {
                "ip": "127.0.0.1",
                "name": "Center",
                "num_leds": 1,
                "rgb_order": 0,
                "start_channel": 6,
                "start_universe": 1,
                "type": 0
            },
            {
                "ip": "127.0.0.1",
                "name": "Right",
                "num_leds": 1,
                "rgb_order": 0,
                "start_channel": 9,
                "start_universe": 1,
                "type": 0
            }
        ]
    },
```

### 3. Audio Visualizer Permission (Flatpak)
If using the Audio Visualizer effect in the OpenRGB Effects plugin, grant PulseAudio / PipeWire access to the Flatpak sandbox:
```bash
flatpak override --user --socket=pulseaudio org.openrgb.OpenRGB
```
