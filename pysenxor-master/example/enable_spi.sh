#!/bin/bash
# Script to enable SPI on Raspberry Pi 5 with Bookworm

CONFIG_FILE="/boot/firmware/config.txt"

echo "Checking SPI configuration..."

if grep -q "^dtparam=spi=on" "$CONFIG_FILE"; then
    echo "SPI is already enabled in $CONFIG_FILE"
else
    echo "Enabling SPI..."
    sudo bash -c "echo 'dtparam=spi=on' >> $CONFIG_FILE"
    echo "SPI enabled in $CONFIG_FILE"
fi

if lsmod | grep -q spi_bcm2835; then
    echo "SPI kernel module is loaded"
else
    echo "Loading SPI kernel module..."
    sudo modprobe spi_bcm2835
fi

if [ -e /dev/spidev0.0 ] || [ -e /dev/spidev0.1 ]; then
    echo "SPI devices found:"
    ls -l /dev/spidev* 2>/dev/null
    echo ""
    echo "SPI is ready to use!"
else
    echo ""
    echo "SPI devices not found. Please reboot your Raspberry Pi:"
    echo "  sudo reboot"
fi
