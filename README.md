# mi48-rpi5-thermal-camera

Simple thermal camera setup for Raspberry Pi 5 with Bookworm OS using the MI48 sensor.

## Hardware Requirements

- Raspberry Pi 5
- MI48 thermal sensor with uHAT board
- Raspberry Pi OS Bookworm (64-bit)

## Quick Setup

### 1. Clone This Repository

```bash
cd ~
git clone https://github.com/ModularMangoTrain/mi48-rpi5-thermal-camera.git
cd mi48-rpi5-thermal-camera
```

### 2. Run Installation Script

```bash
chmod +x install.sh
./install.sh
```

### 3. Reboot

```bash
sudo reboot
```

### 4. Run the Thermal Camera

```bash
sudo python3 stream_spi_rpi5.py
```

Press **'q'** to quit.

## Usage

### Basic Usage
```bash
sudo python3 stream_spi_rpi5.py
```

### Record Thermal Data
```bash
sudo python3 stream_spi_rpi5.py -r
```

### Change Framerate
```bash
sudo python3 stream_spi_rpi5.py -fps 10
```

## Manual Installation

If you prefer to install manually:

### 1. Enable SPI Interface

```bash
sudo raspi-config
```

Navigate to: **Interface Options** → **SPI** → **Enable**

### 2. Install Dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-opencv python3-numpy i2c-tools
pip3 install -r requirements.txt --break-system-packages
```

### 3. Install pysenxor Library

```bash
cd ~
git clone https://github.com/melexis/pysenxor.git
cd pysenxor
sudo python3 setup.py install
```

### 4. Reboot

```bash
sudo reboot
```

## Troubleshooting

### SPI Device Not Found

Verify SPI is enabled:
```bash
ls /dev/spidev*
```

You should see `/dev/spidev0.0` and `/dev/spidev0.1`.

### Permission Denied

Always run with `sudo`:
```bash
sudo python3 stream_spi_rpi5.py
```

### I2C Address Issues

Check your sensor address:
```bash
sudo i2cdetect -y 1
```

If it shows `0x41` instead of `0x40`, edit `stream_spi_rpi5.py` and change:
```python
I2C_ADDRESS = 0x41
```

### Display Issues

If running over SSH, you need X11 forwarding:
```bash
ssh -X pi@raspberrypi.local
```

Or use VNC for better performance.

## Hardware Connections

- **I2C**: Automatically connected via uHAT
- **SPI**: Uses CE1 (GPIO7)
- **DATA_READY**: GPIO24 (Pin 18)
- **RESET**: GPIO23 (Pin 16)

## Credits

Based on [Meridian Innovation's pysenxor library](https://github.com/melexis/pysenxor).
Modified for Raspberry Pi 5 compatibility.

## License

See original pysenxor license.
