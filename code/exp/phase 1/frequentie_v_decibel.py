import struct
import time
import pyaudio
import numpy as np
import pandas as pd

from scipy.signal import butter, sosfilt, bilinear, lfilter

# === Audio Configuration ===
CHUNK = 48000                       # Frames per buffer
SAMPLE_RATE = 48000                # Sample rate in Hz
FORMAT = pyaudio.paInt32           # Audio format
CHANNELS = 1                       # Number of input channels
DEV_INDEX = 0                      # Input device index (check with PyAudio list_devices)

# === Bandpass Filter Configuration ===
LOW_CUTOFF = 200       # Hz
HIGH_CUTOFF = 5000    # Hz
# ORDER = 6             # Filter order
# sos = butter(ORDER, [LOW_CUTOFF, HIGH_CUTOFF], btype='bandpass', fs=SAMPLE_RATE, output='sos')

# === Measurement Parameters ===
NUM_MEASUREMENTS = 20
SAMPLES_PER_MEASUREMENT = 25
FREQ = [i*(HIGH_CUTOFF-LOW_CUTOFF)/(NUM_MEASUREMENTS-1)+LOW_CUTOFF for i in range(NUM_MEASUREMENTS)]
db_offset = 0
reference_db =86.3



freq = FREQ[0]

# === Global Counters ===
count_data = 0       
count_point = 0      

# === Data Storage ===
freq_db = pd.DataFrame(index = FREQ, columns = [i+1 for i in range(SAMPLES_PER_MEASUREMENT)])

def a_weighting(fs):
    """Design of an A-weighting filter for a given sampling rate fs."""
    # Constants for analog A-weighting filter from IEC 61672
    f1 = 20.598997
    f2 = 107.65265
    f3 = 737.86223
    f4 = 12194.217

    A1000 = 1.9997  # Gain at 1000 Hz to normalize

    NUMs = [(2*np.pi*f4)**2 * (10**(A1000/20)), 0, 0, 0, 0]
    DENs = np.convolve(
        [1, 4*np.pi*f4, (2*np.pi*f4)**2],
        [1, 4*np.pi*f1, (2*np.pi*f1)**2]
    )
    DENs = np.convolve(
        np.convolve(DENs, [1, 2*np.pi*f3]),
        [1, 2*np.pi*f2]
    )

    # Apply bilinear transform
    b, a = bilinear(NUMs, DENs, fs)
    return b, a

# === Callback function: Called whenever a new audio chunk is available ===

def callback(in_data, frame_count, time_info, status):
    global count_data, reference_db, count_point, freq

    # datapoint control
    if SAMPLES_PER_MEASUREMENT <= count_data:
        return (in_data, pyaudio.paContinue)

    # Decode raw audio data
    audio_data = np.frombuffer(in_data, dtype=np.int32).astype(np.float32)/2**31
    
    # Convert to Pascals: ±1.0 -> ±20 Pa
    audio_pa = (audio_data ) * 20

    b, a = a_weighting(SAMPLE_RATE)

    # RMS -> dB with offset
    filtered = lfilter(b, a, audio_pa)
    rms = np.sqrt(np.mean(np.square(filtered)))
    if rms > 0:
        measured_db = 20 * np.log10(rms /20e-6)
        freq_db.at[freq, 'ref db'] = reference_db
        freq_db.at[freq, count_data] = measured_db
        count_data += 1
        print(f"[{count_point + 1}/{NUM_MEASUREMENTS}] freq: {freq} dB, Reference: {reference_db:.2f} Measured: {measured_db:.2f} dB")
    else:
        print("RMS = 0, skipping sample")

    return (in_data, pyaudio.paContinue)

# === Main function to control measurement loop ===
def main():
    global count_data, count_point, reference_db, FREQ, freq

    audio = pyaudio.PyAudio()
    # Start initial stream
    stream = audio.open(format=FORMAT, rate=SAMPLE_RATE, channels=CHANNELS,
                        input_device_index=DEV_INDEX, input=True, frames_per_buffer=CHUNK,
                        stream_callback=callback)

    stream.start_stream()
    
    try:
        while count_point < NUM_MEASUREMENTS:
            if count_data >= SAMPLES_PER_MEASUREMENT:
                count_data = 0
                count_point += 1
                if count_point < NUM_MEASUREMENTS:
                    stream.stop_stream()

                    # initialize new frequencies and measure the reference db
                    freq = FREQ[count_point]
                    input(f'\nset the frequencie to {freq}')
                    reference_db = float(input(f"\nNew reference decibel for frequencie {freq}: "))
                    stream.start_stream()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nMeasurement interrupted by user.")

    print("All measurements complete. Saving results...")
    freq_db.to_csv("freq_db.csv", index=True)

    stream.stop_stream()
    stream.close()
    audio.terminate()

if __name__ == "__main__":
    main()
