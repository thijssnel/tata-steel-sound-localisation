import time
import pyaudio
import numpy as np
import pandas as pd
from scipy import signal
from scipy.signal import butter, sosfilt

# === Audio Configuration ===
SAMPLE_RATE = 48000
FORMAT = pyaudio.paInt16
CHANNELS = 4
DEV_INDEX = 0  # Input device index (adjust as needed)

# === Bandpass Filter Configuration ===
LOW_CUTOFF = 50       # Hz
HIGH_CUTOFF = 5000    # Hz
ORDER = 6             # Filter order
sos = butter(ORDER, [LOW_CUTOFF, HIGH_CUTOFF], btype='bandpass', fs=SAMPLE_RATE, output='sos')

# === Measurement Settings ===
FREQ_REF = np.linspace(50, 5000, 10)  # 10 reference frequencies between 50 Hz and 5000 Hz
WAVE_LENGTH_TIME = np.array([1, 5, 10, 50, 100, 500, 1000])  # Wavelength multipliers

NUM_MEASUREMENTS = len(FREQ_REF) * len(WAVE_LENGTH_TIME)
SAMPLES_PER_MEASUREMENT = 1         # Samples per measurement point

# === Global Counters ===
count_data = 0       # Samples collected for current (freq, length)
count_point = 0      # Index of current measurement set

# === Initial Parameters ===
freq_ref = FREQ_REF[0]
length_ref = WAVE_LENGTH_TIME[0]
phi_ref = 45         # Reference azimuth angle
theta_ref = 45       # Reference elevation angle
CHUNK = int(length_ref * SAMPLE_RATE / freq_ref)  # Buffer size in frames for first measurments

# === Data Storage ===
index = pd.MultiIndex.from_product([FREQ_REF, WAVE_LENGTH_TIME], names=('freq_ref', 'wavelength multiplier'))
direction_phi = pd.DataFrame(index=index, columns=[i for i in range(SAMPLES_PER_MEASUREMENT)])
direction_theta = pd.DataFrame(index=index, columns=[i for i in range(SAMPLES_PER_MEASUREMENT)])


# === Function: Cross-correlation lag estimator ===
def get_signal_lag(m0, mn, sample_rate):
    corr = signal.correlate(mn, m0, mode="full")
    lags = signal.correlation_lags(mn.size, m0.size, mode="full")
    lag = lags[np.argmax(corr)]
    return lag


# === Callback function: Called whenever a new audio chunk is available ===
def callback(in_data, frame_count, time_info, status):
    global count_data, count_point, direction_phi, direction_theta, freq_ref, length_ref, SAMPLE_RATE

    if SAMPLES_PER_MEASUREMENT <= count_data:
        return (in_data, pyaudio.paContinue)

    # Convert raw audio bytes to int16 numpy array
    audio_data = np.frombuffer(in_data, dtype=np.int16).reshape(-1, CHANNELS)
    
    # Convert to float for normalization and filtering
    normalized_data = audio_data.astype(np.float32)

    # Normalize and filter each channel
    for ch in range(4):
        max_val = np.max(np.abs(normalized_data[:, ch]))
        if max_val != 0:
            normalized_data[:, ch] /= max_val
        normalized_data[:, ch] = sosfilt(sos, audio_data[:, ch])  # Apply bandpass filter
        
        






    # === Compute signal delays ===
    delta_x = get_signal_lag(normalized_data[:, 0], normalized_data[:, 1], SAMPLE_RATE)
    delta_y = get_signal_lag(normalized_data[:, 0], normalized_data[:, 2], SAMPLE_RATE)
    delta_z = get_signal_lag(normalized_data[:, 0], normalized_data[:, 3], SAMPLE_RATE) / 2

    # === Convert delays to angles ===
    phi = np.arctan2(delta_y, delta_x)
    theta = np.arctan2(np.sqrt(delta_x**2 + delta_y**2), delta_z)

    # === Store results ===
    direction_theta.at[(freq_ref, length_ref), count_data] = np.rad2deg(theta) - theta_ref
    direction_phi.at[(freq_ref, length_ref), count_data] = np.rad2deg(phi) - phi_ref

    count_data += 1
    print(f"[{count_point + 1}/{NUM_MEASUREMENTS}] freq: {freq_ref} Hz, length: {length_ref}, φ diff: {np.rad2deg(phi) - phi_ref:.2f}")
    print(f"[{count_point + 1}/{NUM_MEASUREMENTS}] freq: {freq_ref} Hz, length: {length_ref}, θ diff: {np.rad2deg(theta) - theta_ref:.2f}")
    
    return (in_data, pyaudio.paContinue)


# === Main function to control measurement loop ===
def main():
    global count_data, count_point, freq_ref, length_ref, FREQ_REF, WAVE_LENGTH_TIME, CHUNK

    audio = pyaudio.PyAudio()

    # Start initial stream
    stream = audio.open(format=FORMAT, rate=SAMPLE_RATE, channels=CHANNELS,
                        input_device_index=DEV_INDEX, input=True, frames_per_buffer=CHUNK,
                        stream_callback=callback)

    running = True

    stream.start_stream()
    try:
        while running:
            if count_data >= SAMPLES_PER_MEASUREMENT:
                count_data = 0
                count_point += 1

                if count_point < NUM_MEASUREMENTS:
                    stream.close()

                    # Every full cycle through WAVE_LENGTH_TIME, update frequency
                    if count_point % len(WAVE_LENGTH_TIME) == 0:
                        freq_ref = FREQ_REF[int(count_point / len(WAVE_LENGTH_TIME))]
                        input(f"\nSwitch tone generator to {freq_ref} Hz and press Enter...")

                    # Update length and CHUNK
                    length_ref = WAVE_LENGTH_TIME[count_point % len(WAVE_LENGTH_TIME)]
                    CHUNK = int(length_ref * SAMPLE_RATE / freq_ref)

                    # Restart stream with new chunk size
                    stream = audio.open(format=FORMAT, rate=SAMPLE_RATE, channels=CHANNELS,
                                        input_device_index=DEV_INDEX, input=True,
                                        frames_per_buffer=CHUNK, stream_callback=callback)
                    stream.start_stream()
                else:
                    break

            time.sleep(0.1)
    except KeyboardInterrupt:
        running = False
        print("\nMeasurement interrupted by user.")

    # === Save data ===
    print("All measurements complete. Saving results...")
    direction_theta.to_csv(f"freq_theta_{theta_ref}.csv", index=True)
    direction_phi.to_csv(f"freq_phi_{phi_ref}.csv", index=True)

    stream.stop_stream()
    stream.close()
    audio.terminate()
    print("Saved to CSV files.")

# === Entry Point ===
if __name__ == "__main__":
    main()

