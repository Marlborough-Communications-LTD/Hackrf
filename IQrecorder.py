# The buffer size could be edited if needed

import SoapySDR
from SoapySDR import *  # SOAPY_SDR_ constants
import numpy as np
import time
from datetime import datetime

# ==== CONFIGURATION ====
FREQ = 2.4e9               
SAMPLE_RATE = 2e6          # Sample rate (samples per second)
GAIN = 30                  # RX gain (0–47 for HackRF)
RECORD_SECONDS = 10        # How long to record
BUFF_SIZE = 4096 * 10      # Buffer size for SDR reads

# ==== OUTPUT FILENAME ====
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
freq_label = f"{FREQ/1e6:.3f}MHz"
OUTPUT_FOLDER = "IQ_dumps/"
OUTPUT_FILE = OUTPUT_FOLDER + f"{timestamp}_{freq_label}.cfile"

# ==== SETUP SDR ====
args = dict(driver="hackrf")
sdr = SoapySDR.Device(args)

sdr.setSampleRate(SOAPY_SDR_RX, 0, SAMPLE_RATE)
sdr.setFrequency(SOAPY_SDR_RX, 0, FREQ)
sdr.setGain(SOAPY_SDR_RX, 0, GAIN)

rx_stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(rx_stream)

print(f"Recording {RECORD_SECONDS} seconds of IQ at {FREQ/1e6:.3f} MHz...")
print(f"Saving to file: {OUTPUT_FILE}")

# ==== RECORDING LOOP ====
buff = np.empty(BUFF_SIZE, dtype=np.complex64)
samples_to_record = int(RECORD_SECONDS * SAMPLE_RATE)
samples_recorded = 0

with open(OUTPUT_FILE, 'wb') as f:
    start_time = time.time()

    try:
        while samples_recorded < samples_to_record:
            sr = sdr.readStream(rx_stream, [buff], BUFF_SIZE)

            if sr.ret > 0:
                buff_valid = buff[:sr.ret]
                f.write(buff_valid.tobytes())
                samples_recorded += sr.ret

    except KeyboardInterrupt:
        print("\nRecording interrupted by user.")

    finally:
        duration = time.time() - start_time
        print(f"\nDone. Recorded {samples_recorded} samples in {duration:.2f} seconds.")
        sdr.deactivateStream(rx_stream)
        sdr.closeStream(rx_stream)

