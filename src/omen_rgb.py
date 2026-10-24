#!/usr/bin/env python3
"""
HP OMEN 4-Zone RGB Keyboard Controller for Linux
Controls keyboard backlight and brightness via ACPI WMI (_SB.WMID.WMAA).
"""

import sys
import os
import argparse

ACPI_PATH = "/proc/acpi/call"
ACPI_METHOD = "\\_SB.WMID.WMAA"

# Physical zone mapping:
ZONE_OFFSETS = {
    "right": 0,
    "center": 1,
    "left": 2,
    "wasd": 3,
}

def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    clean = hex_str.lstrip("#")
    if len(clean) != 6:
        raise ValueError(f"Invalid hex color: {hex_str}. Expected 6 hex characters (e.g. FF0000).")
    return int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)

def send_acpi_call(cmd_type: int, payload_bytes: list[int]) -> bool:
    if not os.path.exists(ACPI_PATH):
        print(f"Error: {ACPI_PATH} not found. Ensure acpi_call is loaded.", file=sys.stderr)
        return False

    # 16-byte header + payload
    data_size = len(payload_bytes)
    total_buf = [0] * (16 + data_size)

    # Magic: "SECU"
    total_buf[0:4] = [0x53, 0x45, 0x43, 0x55]
    # Command: 131081 (0x20009)
    cmd = 131081
    total_buf[4:8] = [cmd & 0xFF, (cmd >> 8) & 0xFF, (cmd >> 16) & 0xFF, (cmd >> 24) & 0xFF]
    # CommandType
    total_buf[8:12] = [cmd_type, 0x00, 0x00, 0x00]
    # Data Size
    total_buf[12:16] = [data_size, 0x00, 0x00, 0x00]
    # Payload
    total_buf[16:] = payload_bytes

    formatted_payload = ", ".join(f"0x{b:02x}" for b in total_buf)
    call_str = f"{ACPI_METHOD} 1 3 {{{formatted_payload}}}"

    try:
        with open(ACPI_PATH, "w") as f:
            f.write(call_str)
        with open(ACPI_PATH, "r") as f:
            resp = f.read().strip()
        if "0x50, 0x41, 0x53, 0x53" in resp:  # 'PASS'
            return True
        print(f"ACPI response: {resp}", file=sys.stderr)
        return False
    except PermissionError:
        print("Permission denied. Ensure /proc/acpi/call permissions are set.", file=sys.stderr)
        return False

def set_zone_colors(wasd: str, left: str, center: str, right: str) -> bool:
    payload = [0] * 128
    color_map = {
        "right": hex_to_rgb(right),
        "center": hex_to_rgb(center),
        "left": hex_to_rgb(left),
        "wasd": hex_to_rgb(wasd),
    }

    color_start = 25  # Offset within the 128-byte payload
    for zone_name, zone_idx in ZONE_OFFSETS.items():
        r, g, b = color_map[zone_name]
        base = color_start + (zone_idx * 3)
        payload[base]     = r
        payload[base + 1] = g
        payload[base + 2] = b

    return send_acpi_call(cmd_type=3, payload_bytes=payload)

def set_brightness(level: int) -> bool:
    """
    CommandType 5: Set brightness level (0 - 255)
    228 = Full / Fn+F4 enabled
    100 = Medium / half brightness
    0   = Backlight off
    """
    payload = [level & 0xFF, 0x00, 0x00, 0x00]
    # BIOS expects at least 4 bytes for brightness, padded to 128 for uniform buffer call
    payload += [0] * (128 - len(payload))
    return send_acpi_call(cmd_type=5, payload_bytes=payload)

def main():
    parser = argparse.ArgumentParser(description="HP OMEN 4-Zone RGB Keyboard Controller")
    subparsers = parser.add_subparsers(dest="command", required=True)

    set_parser = subparsers.add_parser("set", help="Set specific colors per zone")
    set_parser.add_argument("--wasd", default="FFFFFF")
    set_parser.add_argument("--left", default="FFFFFF")
    set_parser.add_argument("--center", default="FFFFFF")
    set_parser.add_argument("--right", default="FFFFFF")

    mono_parser = subparsers.add_parser("static", help="Set one color across all 4 zones")
    mono_parser.add_argument("color", help="Hex color code (e.g. FF4500)")

    bright_parser = subparsers.add_parser("brightness", help="Set backlight brightness level (0-255)")
    bright_parser.add_argument("level", type=int, choices=range(0, 256), metavar="[0-255]")

    subparsers.add_parser("off", help="Turn off backlight (via brightness 0, preserving colors)")
    subparsers.add_parser("on", help="Turn on backlight (full brightness 228)")

    args = parser.parse_args()

    success = False
    if args.command == "set":
        success = set_zone_colors(args.wasd, args.left, args.center, args.right)
    elif args.command == "static":
        success = set_zone_colors(args.color, args.color, args.color, args.color)
    elif args.command == "brightness":
        success = set_brightness(args.level)
    elif args.command == "off":
        success = set_brightness(0)
    elif args.command == "on":
        success = set_brightness(228)

    if success:
        print("Backlight state updated successfully.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
