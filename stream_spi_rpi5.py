#!/usr/bin/env python3
"""
MI48 Thermal Camera Stream for Raspberry Pi 5
Optimized for Raspberry Pi OS Bookworm

Usage:
    sudo python3 stream_spi_rpi5.py
    sudo python3 stream_spi_rpi5.py -r  # Record data
    sudo python3 stream_spi_rpi5.py -fps 10  # Set framerate

Press 'q' to quit
"""

import sys
import os
import signal
from smbus2 import SMBus
from spidev import SpiDev
import argparse
import time
import logging
import numpy as np
import cv2 as cv

try:
    from gpiozero import DigitalInputDevice, DigitalOutputDevice
    from gpiozero.pins.lgpio import LGPIOFactory
except ImportError:
    print("ERROR: Missing required libraries!")
    print("Install with: pip3 install gpiozero lgpio --break-system-packages")
    sys.exit(1)

try:
    from senxor.mi48 import MI48, DATA_READY, format_header, format_framestats
    from senxor.utils import data_to_frame, cv_filter
    from senxor.interfaces import SPI_Interface, I2C_Interface
except ImportError:
    print("ERROR: pysenxor library not found!")
    print("Install from: https://github.com/melexis/pysenxor")
    sys.exit(1)

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

# ============================================================================
# CONFIGURATION - Adjust these if needed
# ============================================================================

I2C_CHANNEL = 1
I2C_ADDRESS = 0x40  # Change to 0x41 if your sensor uses that address

SPI_BUS = 0
SPI_DEVICE = 1  # CE1
SPI_MODE = 0b00
SPI_MAX_SPEED_HZ = 31200000

DEFAULT_FPS = 7

# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='MI48 Thermal Camera for Raspberry Pi 5')
    parser.add_argument('-r', '--record', action='store_true', 
                        help='Record thermal data to file')
    parser.add_argument('-fps', '--framerate', type=float, default=DEFAULT_FPS,
                        help=f'Camera framerate (default: {DEFAULT_FPS})')
    return parser.parse_args()

def get_filename(tag):
    """Generate timestamped filename"""
    ts = time.strftime('%Y%m%d-%H%M%S', time.localtime())
    return f"{tag}--{ts}.dat"

def write_frame(outfile, arr):
    """Write thermal data frame to file"""
    if arr.dtype == np.uint16:
        outstr = ('{:n} ' * arr.size).format(*arr.ravel(order='C')) + '\n'
    else:
        outstr = ('{:.2f} ' * arr.size).format(*arr.ravel(order='C')) + '\n'
    outfile.write(outstr)
    outfile.flush()

def display_thermal_image(img, title='MI48 Thermal Camera'):
    """Display thermal image with color mapping"""
    img_colored = cv.applyColorMap(img, cv.COLORMAP_JET)
    img_resized = cv.resize(img_colored, (640, 496), interpolation=cv.INTER_CUBIC)
    cv.imshow(title, img_resized)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("Shutting down...")
    mi48.stop(poll_timeout=0.25, stop_timeout=1.2)
    cv.destroyAllWindows()
    sys.exit(0)

# ============================================================================
# MAIN PROGRAM
# ============================================================================

if __name__ == "__main__":
    args = parse_args()
    
    print("=" * 60)
    print("MI48 Thermal Camera for Raspberry Pi 5")
    print("=" * 60)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize GPIO factory for Raspberry Pi 5
    factory = LGPIOFactory(chip=4)
    
    # Initialize I2C
    print(f"Initializing I2C (address: 0x{I2C_ADDRESS:02X})...")
    i2c = I2C_Interface(SMBus(I2C_CHANNEL), I2C_ADDRESS)
    
    # Initialize SPI
    print(f"Initializing SPI (bus: {SPI_BUS}, device: {SPI_DEVICE})...")
    spi = SPI_Interface(SpiDev(SPI_BUS, SPI_DEVICE), xfer_size=160)
    spi.device.mode = SPI_MODE
    spi.device.max_speed_hz = SPI_MAX_SPEED_HZ
    spi.device.bits_per_word = 8
    spi.device.lsbfirst = False
    
    # Setup GPIO pins
    print("Configuring GPIO pins...")
    mi48_data_ready = DigitalInputDevice("BCM24", pull_up=False, pin_factory=factory)
    mi48_reset_n = DigitalOutputDevice("BCM23", active_high=False, 
                                       initial_value=True, pin_factory=factory)
    
    # Reset handler
    class MI48_reset:
        def __init__(self, pin):
            self.pin = pin
        
        def __call__(self):
            print('Resetting MI48 sensor...')
            self.pin.on()
            time.sleep(0.000035)
            self.pin.off()
            time.sleep(0.050)
            print('Reset complete.')
    
    # Initialize MI48 sensor
    print("Initializing MI48 sensor...")
    mi48 = MI48([i2c, spi], data_ready=mi48_data_ready,
                reset_handler=MI48_reset(pin=mi48_reset_n))
    
    # Get camera info
    camera_info = mi48.get_camera_info()
    print(f"Camera ID: {mi48.camera_id_hex}")
    print(f"Firmware: {mi48.fw_version}")
    
    # Set framerate
    mi48.set_fps(args.fps)
    print(f"Framerate: {args.fps} FPS")
    
    # Enable filtering if available
    if int(mi48.fw_version[0]) >= 2:
        mi48.enable_filter(f1=True, f2=True, f3=False)
        mi48.set_offset_corr(0.0)
        print("Filtering enabled")
    
    # Setup recording if requested
    fd_data = None
    if args.record:
        filename = get_filename(mi48.camera_id_hex)
        fd_data = open(filename, 'w')
        print(f"Recording to: {filename}")
    
    # Start streaming
    print("\nStarting thermal camera stream...")
    print("Press 'q' to quit\n")
    mi48.start(stream=True, with_header=True)
    
    # Main loop
    try:
        while True:
            # Wait for data ready
            if hasattr(mi48, 'data_ready'):
                mi48.data_ready.wait_for_active()
            else:
                while not (mi48.get_status() & DATA_READY):
                    time.sleep(0.01)
            
            # Read frame
            data, header = mi48.read()
            
            if data is None:
                continue
            
            # Save to file if recording
            if fd_data:
                write_frame(fd_data, data)
            
            # Convert to image
            img = data_to_frame(data, mi48.fpa_shape)
            
            # Log frame stats
            if header is not None:
                logger.debug('  '.join([format_header(header),
                                       format_framestats(data)]))
            
            # Normalize image for display
            img_float = img.astype(np.float32)
            img_min, img_max = img_float.min(), img_float.max()
            
            if img_max > img_min:
                img8u = ((img_float - img_min) * 255.0 / (img_max - img_min)).astype(np.uint8)
            else:
                img8u = np.zeros_like(img_float, dtype=np.uint8)
            
            # Apply filtering
            img8u = cv_filter(img8u, parameters={'blur_ks': 3}, 
                            use_median=False, use_bilat=True, use_nlm=False)
            
            # Display
            display_thermal_image(img8u)
            
            # Check for quit
            key = cv.waitKey(1)
            if key == ord('q'):
                break
    
    finally:
        # Cleanup
        print("\nCleaning up...")
        mi48.stop(stop_timeout=0.5)
        if fd_data:
            fd_data.close()
            print("Recording saved")
        cv.destroyAllWindows()
        print("Done!")
