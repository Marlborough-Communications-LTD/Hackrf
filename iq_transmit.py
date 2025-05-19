import SoapySDR
from SoapySDR import *  # SOAPY_SDR_ constants
import numpy as np
import time
import os
import argparse

# ==== PARSE COMMAND-LINE ARGUMENTS ====
parser = argparse.ArgumentParser(description="Transmit IQ file using HackRF")
parser.add_argument("iq_file", help="Path to the .cfile IQ file")
parser.add_argument("--loop", action="store_true", help="Loop playback")
args = parser.parse_args()

IQ_FILE = args.iq_file
LOOP = args.loop

# ==== CONFIGURATION ====
FREQ = 433e6                # Frequency to transmit at
SAMPLE_RATE = 2e6           # Match the sample rate used for recording
GAIN = 30                   # TX gain (0–47 for HackRF)

# ==== LOAD IQ FILE ====
if not os.path.exists(IQ_FILE):
    raise FileNotFoundError(f"IQ file not found: {IQ_FILE}")

iq_data = np.fromfile(IQ_FILE, dtype=np.complex64)
total_samples = len(iq_data)

print(f"Loaded {total_samples} samples from {IQ_FILE}")

# ==== SETUP SDR ====
args_sdr = dict(driver="hackrf")
sdr = SoapySDR.Device(args_sdr)

sdr.setSampleRate(SOAPY_SDR_TX, 0, SAMPLE_RATE)
sdr.setFrequency(SOAPY_SDR_TX, 0, FREQ)
sdr.setGain(SOAPY_SDR_TX, 0, GAIN)

tx_stream = sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32)
sdr.activateStream(tx_stream)

print(f"Transmitting on {FREQ/1e6:.3f} MHz... Press Ctrl+C to stop.")

BUFF_SIZE = 4096
try:
    index = 0
    while True:
        end = min(index + BUFF_SIZE, total_samples)
        chunk = iq_data[index:end]

        if len(chunk) == 0:
            if LOOP:
                index = 0
                continue
            else:
                break

        sr = sdr.writeStream(tx_stream, [chunk], len(chunk))
        if sr.ret <= 0:
            print(f"TX stream write error: {sr.ret}")
            break

        index += BUFF_SIZE

except KeyboardInterrupt:
    print("\nTransmission stopped by user.")

finally:
    sdr.deactivateStream(tx_stream)
    sdr.closeStream(tx_stream)
    print("HackRF transmission ended.")

