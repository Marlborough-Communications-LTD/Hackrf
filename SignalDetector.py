# Filters though command signals that are used on radio
# Prints when something is detected

import SoapySDR
from SoapySDR import *  # SOAPY_SDR_ constants
import numpy as np
import time

# Frequencies to monitor
FREQ_433 = 433e6     # 433 MHz
FREQ_24 = 2410e6     # 2.4 GHz
FREQ_58 = 5800e6     # 5.8 GHz

FREQUENCIES = [FREQ_433, FREQ_24, FREQ_58]

SAMPLE_RATE = 0.5e6          # 500 kSPS
THRESHOLD = 4e-4             # Signal power threshold for detection
BUFF_SIZE = 4096 * 10        # Buffer size
DETECTION_COOLDOWN = 2       # Seconds to ignore after detection
DWELL_TIME = 1.5             # Seconds to stay on each frequency

# Setup SDR (for Hackrf)
args = dict(driver="hackrf")
sdr = SoapySDR.Device(args)
sdr.setSampleRate(SOAPY_SDR_RX, 0, SAMPLE_RATE)

# Starting the stream
rx_stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(rx_stream)

print("Starting frequency sweep. Press Ctrl+C to stop.")

# Function that checks for signals at input Hz
def detect_on_frequency(freq_hz):
    sdr.setFrequency(SOAPY_SDR_RX, 0, freq_hz)
    print(f"Scanning {freq_hz/1e6:.3f} MHz...")
    buff = np.empty(BUFF_SIZE, np.complex64)
    start_time = time.time()
    last_detect_time = 0

    while time.time() - start_time < DWELL_TIME:
        sr = sdr.readStream(rx_stream, [buff], BUFF_SIZE)
        if sr.ret > 0:
            signal_power = np.mean(np.abs(buff[:sr.ret])**2)

            if signal_power > THRESHOLD and (time.time() - last_detect_time > DETECTION_COOLDOWN):
                print(f"[{time.strftime('%H:%M:%S')}] Signal detected at {freq_hz/1e6:.3f} MHz! Power: {signal_power:.6f}")
                last_detect_time = time.time()

        time.sleep(0.05)

try:
    while True:
        for freq in FREQUENCIES:
            detect_on_frequency(freq)

except KeyboardInterrupt:
    print("\nStopping frequency sweep...")

finally:
    sdr.deactivateStream(rx_stream)
    sdr.closeStream(rx_stream)

