import SoapySDR
from SoapySDR import *  # SOAPY_SDR_ constants
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy.signal import get_window

# ==== CONFIGURATION ====
FREQ = 433e6              # Center frequency
SAMPLE_RATE = 2e6         # Sample rate
GAIN = 30                 # Gain
FFT_SIZE = 1024           # FFT resolution
WATERFALL_FRAMES = 100    # Number of rows in waterfall
WINDOW = 'hann'           # Window type (Hann reduces leakage)

# ==== SETUP SDR ====
args = dict(driver="hackrf")
sdr = SoapySDR.Device(args)

sdr.setSampleRate(SOAPY_SDR_RX, 0, SAMPLE_RATE)
sdr.setFrequency(SOAPY_SDR_RX, 0, FREQ)
sdr.setGain(SOAPY_SDR_RX, 0, GAIN)

rx_stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(rx_stream)

# ==== INIT PLOTTING ====
waterfall = np.zeros((WATERFALL_FRAMES, FFT_SIZE))
fig, ax = plt.subplots()
img = ax.imshow(waterfall, aspect='auto', extent=[-SAMPLE_RATE/2/1e6, SAMPLE_RATE/2/1e6, 0, WATERFALL_FRAMES],
                cmap='inferno', vmin=-120, vmax=0, origin='lower')
ax.set_xlabel('Frequency (MHz)')
ax.set_ylabel('Time (scrolling)')
fig.suptitle(f'Live Waterfall - {FREQ/1e6:.3f} MHz')

window = get_window(WINDOW, FFT_SIZE)

# ==== READ + PLOT LOOP ====
buff = np.empty(FFT_SIZE, np.complex64)

def update(frame):
    sr = sdr.readStream(rx_stream, [buff], FFT_SIZE)
    if sr.ret > 0:
        windowed = buff[:sr.ret] * window
        spectrum = np.fft.fftshift(np.fft.fft(windowed, FFT_SIZE))
        power_db = 10 * np.log10(np.abs(spectrum)**2 + 1e-12)

        # Scroll waterfall up and insert new row
        global waterfall
        waterfall = np.roll(waterfall, -1, axis=0)
        waterfall[-1, :] = power_db

        img.set_data(waterfall)
    return [img]

ani = animation.FuncAnimation(fig, update, interval=50, blit=True)
plt.show()

# Cleanup after closing plot
sdr.deactivateStream(rx_stream)
sdr.closeStream(rx_stream)

