import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy.signal import get_window
import os

# ==== CONFIGURATION ====
IQ_FOLDER = "IQ_dumps/"
IQ_FILE = IQ_FOLDER + "20250516_061955_433.000MHz.cfile"  # Your .cfile input
SAMPLE_RATE = 2e6         # Sample rate used during recording
FFT_SIZE = 1024           # FFT resolution
WATERFALL_FRAMES = 100    # Number of rows in the waterfall
WINDOW = 'hann'           # Windowing function
CHUNK_SIZE = FFT_SIZE     # Number of samples per frame

# ==== LOAD FILE ====
if not os.path.exists(IQ_FILE):
    raise FileNotFoundError(f"File not found: {IQ_FILE}")

iq_data = np.fromfile(IQ_FILE, dtype=np.complex64)
total_samples = len(iq_data)
print(f"Loaded {total_samples} samples.")

# ==== INIT PLOTTING ====
waterfall = np.zeros((WATERFALL_FRAMES, FFT_SIZE))
fig, ax = plt.subplots()
img = ax.imshow(waterfall, aspect='auto',
                extent=[-SAMPLE_RATE/2/1e6, SAMPLE_RATE/2/1e6, 0, WATERFALL_FRAMES],
                cmap='inferno', vmin=-120, vmax=0, origin='lower')
ax.set_xlabel('Frequency (MHz)')
ax.set_ylabel('Time (scrolling)')
fig.suptitle(f'Waterfall Plot of {IQ_FILE}')

window = get_window(WINDOW, FFT_SIZE)

# ==== PLOTTING LOOP ====
index = 0

def update(frame):
    global index, waterfall

    if index + CHUNK_SIZE > total_samples:
        return [img]  # End of file — just hold

    chunk = iq_data[index:index + CHUNK_SIZE]
    windowed = chunk * window
    spectrum = np.fft.fftshift(np.fft.fft(windowed, FFT_SIZE))
    power_db = 10 * np.log10(np.abs(spectrum)**2 + 1e-12)

    # Update the waterfall
    waterfall = np.roll(waterfall, -1, axis=0)
    waterfall[-1, :] = power_db

    img.set_data(waterfall)
    index += CHUNK_SIZE
    return [img]

ani = animation.FuncAnimation(fig, update, interval=50, blit=True)
plt.show()

