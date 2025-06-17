import struct
import time
import pyaudio
import numpy as np
import pandas as pd

CHUNK = 48000  # frames per buffer
SAMPLE_RATE = 48000
FORMAT = pyaudio.paInt16
NP_FORMAT = np.int16
CHANNELS = 1

NUM_MEASUREMENTS = 10
SAMPLES_PER_MEASUREMENT = 24

db_offset = 120
reference_db =60
freq_db = {}
count_data = 0
count_point = 0
freq = 60

def callback(in_data, frame_count, time_info, status):
    global count_data, reference_db, count_point, freq

    # Decode raw audio data
    data = np.frombuffer(in_data, dtype=np.int16).astype(np.float32)

    # RMS -> dB
    rms = np.sqrt(np.mean(np.square(data)))
    if rms > 0:
        measured_db = db_offset -  20 * np.log10(rms / 32767)
        db_diff = measured_db - reference_db
        freq_db.setdefault(str(freq), []).append(db_diff)
        count_data += 1
        print(f"[{count_point + 1}/{NUM_MEASUREMENTS}] freq: {freq} dB, Measured: {db_diff:.2f} dB")
    else:
        print("RMS = 0, skipping sample")

    return (in_data, pyaudio.paContinue)

def main():
    global count_data, count_point, reference_db

    audio = pyaudio.PyAudio()
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
                    freq = int(input(f"\nNieuwe freq voor meting {count_point + 1}: "))
                    reference_db = int(input(f"\nNieuwe referentie dB voor meting {count_point + 1}: "))
                    stream.start_stream()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nOnderbroken door gebruiker.")

    print("Metingen klaar, opslaan...")
    df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in freq_db.items()]))
    df.to_csv("freq_db.csv", index=False)

    stream.stop_stream()
    stream.close()
    audio.terminate()
    print("Opgeslagen in 'freq_db.csv'.")

if __name__ == "__main__":
    main()
