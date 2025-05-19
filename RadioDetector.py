# Filters though command signals that are used on radio
# Prints when something is detected
# Saves a clip of the data to a file when something strong is detected, has a cooldown to save space
# 

import SoapySDR
from SoapySDR import *  # SOAPY_SDR_ constants
import numpy as np
import time
from datetime import datetime

# ==== Frequencies to monitor in sweep ====
FREQ_433 = 433e6     # 433 MHz
FREQ_900 = 900e6     # 900 MHz
FREQ_24 = 2410e6     # 2.4 GHz
FREQ_58 = 5800e6     # 5.8 GHz
FREQUENCIES = [FREQ_433, FREQ_24, FREQ_58, FREQ_900]

# ==== HACKRF CONFIGURATION ====
SAMPLE_RATE = 10e6           # 10 MSPS (this is low)
THRESHOLD = 1e-2             # Signal power threshold for detection
HIGH_THRESHOLD = 0.1         # For determining if th signal is strong
BUFF_SIZE = 4096 * 10        # Buffer size for SDR reads
DETECTION_COOLDOWN = 2       # Seconds to ignore after detection
DWELL_TIME = 0.5             # Seconds to stay on each frequency

# ==== SETUP HACKRF ====
args = dict(driver="hackrf")
sdr = SoapySDR.Device(args)
sdr.setSampleRate(SOAPY_SDR_RX, 0, SAMPLE_RATE)

# ==== DUMP FILE ====
DUMP_TO_FILE = 0            # Set to 0 to disable the file dumps
OUTPUT_FOLDER = "IQ_dumps/"  # Location of file dumps
REC_SIZE = 3                 # Size in seconds of recording
REPEAT_WAIT = 5              # number of loops until next file dump
counter = 5

# Starting the stream
rx_stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(rx_stream)

print("Starting frequency sweep. Press Ctrl+C to stop.")
print("Sweeping the following:")

for x in FREQUENCIES:
    print(x*1e-6)

print("Scanning...")

# Function that checks for signals at input Hz
def detect_on_frequency(freq_hz, counter):
	
    counter += 1
    sdr.setFrequency(SOAPY_SDR_RX, 0, freq_hz)
    buff = np.empty(BUFF_SIZE, np.complex64)
    start_time = time.time()
    last_detect_time = 0

    while time.time() - start_time < DWELL_TIME:
        sr = sdr.readStream(rx_stream, [buff], BUFF_SIZE)
        if sr.ret > 0:
            signal_power = np.mean(np.abs(buff[:sr.ret])**2)
            
            # Check output power
            if signal_power > THRESHOLD and (time.time() - last_detect_time > DETECTION_COOLDOWN):
                # Calculate power in dBFS
                signal_power_dbfs = 10 * np.log10(signal_power)

                # Estimate dBm assuming full-scale for Hackrf = -20 dBm
                # Because the hackrf is not calibrarted its hard to convert to dbm (not accurate), the value being printed for power is a digital value between -1 and 1
                full_scale_dBm = -20
                signal_power_dBm_est = signal_power_dbfs + full_scale_dBm

                if (signal_power > HIGH_THRESHOLD):
                    print(f"[{time.strftime('%H:%M:%S')}] Strong signal detected at {freq_hz/1e6:.3f} MHz! Power: {signal_power:.6f}")
                    print(f"Estimated signal power: {signal_power_dBm_est:.2f} dBm")
                
                    # When a strong signal is detected saving the signal to a file if flag high
                    if ((DUMP_TO_FILE == 1) and (REPEAT_WAIT >= counter/len(FREQUENCIES))) :                    
                        # ==== OUTPUT FILENAME ====
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        freq_label = f"{freq_hz/1e6:.3f}MHz"
                        OUTPUT_FILE = OUTPUT_FOLDER + f"{timestamp}_{freq_label}.cfile"
                    
                        print(f"Saving to file: {OUTPUT_FILE}")
                   
                        num_samples_to_capture = int(SAMPLE_RATE * REC_SIZE)
                        samples_captured = 0

                        with open(OUTPUT_FILE, 'wb') as f:
                            while samples_captured < num_samples_to_capture:
                                sr = sdr.readStream(rx_stream, [buff], BUFF_SIZE)
                                if sr.ret > 0:
                                    buff[:sr.ret].tofile(f)
                                    samples_captured += sr.ret
                    
                        print("File dump complete, resuming scan") 
           
                else: # Weak signal detected
                    print(f"[{time.strftime('%H:%M:%S')}] Signal detected at {freq_hz/1e6:.3f} MHz! Power: {signal_power:.6f}")
                    print(f"Estimated signal power: {signal_power_dBm_est:.2f} dBm")
                    
                last_detect_time = time.time()
                time.sleep(0.05)

# Forever loop filtering through frequency's
try:
    while True:
        for freq in FREQUENCIES:
            detect_on_frequency(freq, counter)

except KeyboardInterrupt:
    print("\nStopping frequency sweep...")

finally:
    sdr.deactivateStream(rx_stream)
    sdr.closeStream(rx_stream)

