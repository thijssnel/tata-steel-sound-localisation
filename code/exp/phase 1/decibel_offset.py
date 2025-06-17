import struct
import time
import pyaudio
import numpy as np
import pandas as pd
from pydub.pyaudioop import rms

from scipy.signal import butter, sosfilt

# === Audio Configuration ===
CHUNK = 48000                       # Frames per buffer
SAMPLE_RATE = 48000                # Sample rate in Hz
FORMAT = pyaudio.paInt32           # Audio format
CHANNELS = 1                       # Number of input channels
DEV_INDEX = 0                      # Input device index (check with PyAudio list_devices)

# === Bandpass Filter Configuration ===
# LOW_CUTOFF = 50       # Hz
# HIGH_CUTOFF = 5000    # Hz
# ORDER = 6             # Filter order
# sos = butter(ORDER, [LOW_CUTOFF, HIGH_CUTOFF], btype='bandpass', fs=SAMPLE_RATE, output='sos')

# === Measurement Parameters ===
NUM_MEASUREMENTS = 10
SAMPLES_PER_MEASUREMENT = 24

offset = {}
count_data = 0
count_point = 0
reference_db = 98.4





# === Callback function: Called whenever a new audio chunk is available ===
def callback(in_data, frame_count, time_info, status):
    global count_data, reference_db, count_point

    # datapoint control
    if SAMPLES_PER_MEASUREMENT <= count_data:
        return (in_data, pyaudio.paContinue)

    # Convert byte stream to int32 assuming 24-bit left-aligned in 32-bit words
    audio_data = np.frombuffer(in_data, dtype=np.int32).astype(np.float64)

    # Convert to Pascals: ±1.0 -> ±20 Pa
    audio_pa = audio_data*(20e-6)

    # Apply filter
    # data = sosfilt(sos, data)

    # RMS -> dB
    rms = np.sqrt(np.mean(np.square(audio_data)))

    if rms > 0:
        measured_db = np.sqrt(np.mean(np.square(120 +  20 * np.log10(abs(audio_data)/ (2**31-1)))))
        offset_val = reference_db - measured_db
        offset.setdefault(str(reference_db), []).append(offset_val)
        count_data += 1
        print(f"[{count_point + 1}/{NUM_MEASUREMENTS}] Ref: {reference_db} dB, Measured: {measured_db:.2f} dB, Offset: {offset_val:.2f}")
    else:
        print("RMS = 0, skipping sample")

    return (in_data, pyaudio.paContinue)

# === Main function to control measurement loop ===
def main():
    global count_data, count_point, reference_db

    audio = pyaudio.PyAudio()
    
    # Start initial stream
    stream = audio.open(format=FORMAT, rate=SAMPLE_RATE, channels=CHANNELS,
                        input=True, frames_per_buffer=CHUNK, stream_callback=callback)
    stream.start_stream()

    try:
        while count_point < NUM_MEASUREMENTS:
            if count_data >= SAMPLES_PER_MEASUREMENT:
                count_data = 0
                count_point += 1
                if count_point < NUM_MEASUREMENTS:
                    stream.stop_stream()

                    # initialize new intesity
                    reference_db = float(input(f"\nNieuwe referentie dB voor meting {count_point + 1}: "))
                    stream.start_stream()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nMeasurement interrupted by user.")

    # === Save data ===
    print("All measurements complete. Saving results...")
    df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in offset.items()]))
    df.to_csv("offsets.csv", index=False)

    stream.stop_stream()
    stream.close()
    audio.terminate()
    print("Bestanden opgeslagen als 'dir_theta.csv' en 'dir_phi.csv'.")


if __name__ == "__main__":
    main()
