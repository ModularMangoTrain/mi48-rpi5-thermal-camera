#!/bin/bash
# Fix SPI configuration for MI48 on CE1

CONFIG_FILE="/boot/firmware/config.txt"

echo "Fixing SPI configuration..."

# Remove the problematic line
sudo sed -i '/^dtoverlay=spi0-0cs/d' "$CONFIG_FILE"

# Add correct overlay if not present
if ! grep -q "^dtoverlay=spi0-1cs" "$CONFIG_FILE"; then
    sudo sed -i '/^dtparam=spi=on/a dtoverlay=spi0-1cs' "$CONFIG_FILE"
    echo "Added dtoverlay=spi0-1cs"
fi

echo "Configuration updated. Please reboot:"
echo "  sudo reboot"
