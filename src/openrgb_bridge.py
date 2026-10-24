#!/usr/bin/env python3
"""
E1.31 / sACN UDP Listener Bridge for HP OMEN 4-Zone RGB Keyboard
Calibrated precisely to Offset 125 (0-indexed channel 1).
"""

import os
import socket
import sys

ACPI_PATH = "/proc/acpi/call"
ACPI_METHOD = "\\_SB.WMID.WMAA"

# Physical OMEN WMI offsets: Right=0, Center=1, Left=2, WASD=3
ZONE_OFFSETS = {
    "right": 0,
    "center": 1,
    "left": 2,
    "wasd": 3,
}

E131_PORT = 5568
PAYLOAD_OFFSET = 125  # Verified via live packet capture


def send_acpi_buffer(cmd_type: int, payload: list[int]):
    data_size = len(payload)
    buf = [0] * (16 + data_size)

    # "SECU"
    buf[0:4] = [0x53, 0x45, 0x43, 0x55]
    cmd = 131081
    buf[4:8] = [
        cmd & 0xFF,
        (cmd >> 8) & 0xFF,
        (cmd >> 16) & 0xFF,
        (cmd >> 24) & 0xFF,
    ]
    buf[8:12] = [cmd_type, 0x00, 0x00, 0x00]
    buf[12:16] = [data_size, 0x00, 0x00, 0x00]
    buf[16:] = payload

    payload_str = ", ".join(f"0x{b:02x}" for b in buf)
    call_bytes = f"{ACPI_METHOD} 1 3 {{{payload_str}}}\n".encode("ascii")

    try:
        fd = os.open(ACPI_PATH, os.O_WRONLY)
        os.write(fd, call_bytes)
        os.close(fd)
    except Exception as e:
        print(f"[!] ACPI write error: {e}", file=sys.stderr)


def set_zones(wasd: tuple, left: tuple, center: tuple, right: tuple):
    payload = [0] * 128
    color_start = 25  # Byte 41 total in ACPI payload

    for zone_idx, (r, g, b) in [
        (ZONE_OFFSETS["right"], right),
        (ZONE_OFFSETS["center"], center),
        (ZONE_OFFSETS["left"], left),
        (ZONE_OFFSETS["wasd"], wasd),
    ]:
        base = color_start + (zone_idx * 3)
        payload[base] = r
        payload[base + 1] = g
        payload[base + 2] = b

    send_acpi_buffer(cmd_type=3, payload=payload)


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind(("0.0.0.0", E131_PORT))
    except OSError as e:
        print(f"[!] Could not bind UDP port {E131_PORT}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[+] Bridge running on UDP 0.0.0.0:{E131_PORT} (offset {PAYLOAD_OFFSET})...")

    last_frame = None

    try:
        while True:
            data, _ = sock.recvfrom(2048)

            if len(data) >= PAYLOAD_OFFSET + 12:
                dmx = data[PAYLOAD_OFFSET : PAYLOAD_OFFSET + 12]

                # Map 4 LEDs
                led0 = (dmx[0], dmx[1], dmx[2])
                led1 = (dmx[3], dmx[4], dmx[5])
                led2 = (dmx[6], dmx[7], dmx[8])
                led3 = (dmx[9], dmx[10], dmx[11])

                frame = (led0, led1, led2, led3)
                if frame != last_frame:
                    set_zones(wasd=led0, left=led1, center=led2, right=led3)
                    last_frame = frame

    except KeyboardInterrupt:
        print("\n[*] Bridge stopped.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()