import struct
import time
import pyaudio
import numpy as np
import pandas as pd
from scipy.signal import butter, sosfilt


# === Audio Configuration ===
CHUNK = 48000                       # Frames per buffer
SAMPLE_RATE = 48000                # Sample rate in Hz
FORMAT = pyaudio.paInt16           # Audio format
CHANNELS = 1                       # Number of input channels
DEV_INDEX = 0                      # Input device index (check with PyAudio list_devices)

# === Measurement Parameters ===
REF_DISTANCE = [i*0.1 +0.2 for i in range(11)]
NUM_MEASUREMENTS = 10
SAMPLES_PER_MEASUREMENT = 25
reference_db = 105


ref_distance = REF_DISTANCE[0]
db_offset = 123.6


# === Global Counters ===
count_data = 0
count_point = 0


# === Bandpass Filter Configuration ===
LOW_CUTOFF = 50       # Hz
HIGH_CUTOFF = 5000    # Hz
ORDER = 6             # Filter order
sos = butter(ORDER, [LOW_CUTOFF, HIGH_CUTOFF], btype='bandpass', fs=SAMPLE_RATE, output='sos')

# === Data Storage ===
distance_df = pd.DataFrame(index = REF_DISTANCE, columns=[i for i in range(SAMPLES_PER_MEASUREMENT)])

# === Callback function: Called whenever a new audio chunk is available ===
def callback(in_data, frame_count, time_info, status):
    global count_data, reference_db, count_point, ref_distance
    if SAMPLES_PER_MEASUREMENT <= count_data:
        return (in_data, pyaudio.paContinue)

    # Decode raw audio data
    data = np.frombuffer(in_data, dtype=np.int16).astype(np.float32)

    # Apply filter
    data = sosfilt(sos, data)

    # RMS -> dB
    rms = np.sqrt(np.mean(np.square(data)))
    if rms > 0:
        measured_db = db_offset +  20 * np.log10(rms / 32767)
        db_diff = measured_db - reference_db
        distance_df.at[ref_distance, count_data] = db_diff
        

        
        count_data += 1
        print(f"[{count_point + 1}/{NUM_MEASUREMENTS}] Ref: {reference_db} dB, Distance: {ref_distance} m, difference in db: {db_diff}")
    else:
        print("RMS = 0, skipping sample")

    return (in_data, pyaudio.paContinue)

# === Main function to control measurement loop ===
def main():
    global count_data, count_point, reference_db, ref_distance, REF_DISTANCE

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
                    ref_distance = REF_DISTANCE[count_point]
                    input(f'distance should be {ref_distance}')
                    reference_db = float(input(f"\nNieuwe referentie dB voor meting {count_point + 1}: "))
                    
                    stream.start_stream()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nOnderbroken door gebruiker.")

    print("Metingen klaar, opslaan...")
    distance_df.to_csv("distance_db.csv", index=False)

    stream.stop_stream()
    stream.close()
    audio.terminate()
    print("Opgeslagen in 'offsets.csv'.")

if __name__ == "__main__":
    main()
