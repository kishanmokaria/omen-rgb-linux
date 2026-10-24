#!/usr/bin/env bash
set -euo pipefail

echo "=================================================="
echo "  HP OMEN 4-Zone RGB Keyboard Controller Installer"
echo "=================================================="

# 1. Install prerequisites
echo "[+] Installing dependencies..."
sudo apt-get update -y
sudo apt-get install -y acpi-call-dkms python3

# 2. Patch acpi-call buffer limit if still at default 256
ACPI_SRC_DIR=$(ls -d /usr/src/acpi-call-* 2>/dev/null | sort -V | tail -n 1 || true)
if [ -n "$ACPI_SRC_DIR" ] && grep -q "#define BUFFER_SIZE 256" "$ACPI_SRC_DIR/acpi_call.c"; then
    echo "[+] Patching acpi_call BUFFER_SIZE to 4096..."
    sudo sed -i 's/#define BUFFER_SIZE 256/#define BUFFER_SIZE 4096/g' "$ACPI_SRC_DIR/acpi_call.c"
    MODULE_VER=$(basename "$ACPI_SRC_DIR" | cut -d'-' -f3)
    echo "[+] Rebuilding DKMS module (acpi-call/$MODULE_VER)..."
    sudo dkms remove "acpi-call/$MODULE_VER" --all || true
    sudo dkms install "acpi-call/$MODULE_VER"
    sudo modprobe -r acpi_call || true
    sudo modprobe acpi_call
fi

# 3. Autoload kernel module on boot
echo "[+] Configuring module autoloading on boot..."
echo "acpi_call" | sudo tee /etc/modules-load.d/acpi_call.conf > /dev/null

# 4. Set persistent procfs permissions via tmpfiles.d
echo "[+] Configuring permissions for /proc/acpi/call..."
echo 'z /proc/acpi/call 0666 root root -' | sudo tee /etc/tmpfiles.d/acpi_call.conf > /dev/null
sudo systemd-tmpfiles --create /etc/tmpfiles.d/acpi_call.conf

# 5. Install the CLI tool
echo "[+] Installing omen-rgb to /usr/local/bin..."
sudo cp src/omen_rgb.py /usr/local/bin/omen-rgb
sudo chmod +x /usr/local/bin/omen-rgb

# 6. Install sleep/resume hook
echo "[+] Setting up resume from sleep hook..."
sudo cp systemd/omen-rgb-resume.sh /lib/systemd/system-sleep/omen-rgb-resume
sudo chmod +x /lib/systemd/system-sleep/omen-rgb-resume

# 7. Optional startup service
echo "[+] Installing systemd startup service..."
sudo cp systemd/omen-rgb.service /etc/systemd/system/omen-rgb.service
sudo systemctl daemon-reload
sudo systemctl enable omen-rgb.service

echo ""
echo "=================================================="
echo "  Installation Successful!"
echo "  Try running: omen-rgb static 00E5FF"
echo "  Or: omen-rgb set --wasd FF0000 --left 00FF00 --center 0000FF --right FFFFFF"
echo "=================================================="
