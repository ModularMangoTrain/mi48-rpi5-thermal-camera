#!/bin/bash
# Installation script for MI48 Thermal Camera on Raspberry Pi 5

echo "=========================================="
echo "MI48 Thermal Camera Setup"
echo "Raspberry Pi 5 - Bookworm OS"
echo "=========================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "ERROR: This doesn't appear to be a Raspberry Pi"
    exit 1
fi

# Update system
echo "Step 1: Updating system packages..."
sudo apt-get update

# Install system dependencies
echo ""
echo "Step 2: Installing system dependencies..."
sudo apt-get install -y python3-pip python3-opencv python3-numpy i2c-tools

# Install Python packages
echo ""
echo "Step 3: Installing Python packages..."
pip3 install -r requirements.txt --break-system-packages

# Install pysenxor
echo ""
echo "Step 4: Installing pysenxor library..."
if [ ! -d "pysenxor" ]; then
    git clone https://github.com/melexis/pysenxor.git
fi
cd pysenxor
sudo python3 setup.py install
cd ..

# Enable SPI
echo ""
echo "Step 5: Enabling SPI interface..."
if ! grep -q "^dtparam=spi=on" /boot/firmware/config.txt; then
    echo "dtparam=spi=on" | sudo tee -a /boot/firmware/config.txt
    echo "SPI enabled in config.txt"
else
    echo "SPI already enabled"
fi

# Enable I2C
echo ""
echo "Step 6: Enabling I2C interface..."
if ! grep -q "^dtparam=i2c_arm=on" /boot/firmware/config.txt; then
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/firmware/config.txt
    echo "I2C enabled in config.txt"
else
    echo "I2C already enabled"
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "IMPORTANT: Please reboot your Raspberry Pi:"
echo "  sudo reboot"
echo ""
echo "After reboot, run the thermal camera with:"
echo "  sudo python3 stream_spi_rpi5.py"
echo ""
