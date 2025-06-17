import time
import pyaudio
import numpy as np
import pandas as pd

# === Audio Configuration ===
CHUNK = 4800                  # Should divide evenly into SAMPLE_RATE
SAMPLE_RATE = 48000           # Sample rate in Hz
FORMAT = pyaudio.paInt32      # Audio format
CHANNELS = 4                  # Number of input channels
DEV_INDEX = 0                 # Input device index

# === Measurement Parameters ===
THETA_REF = 4                 # Theta values to iterate
PHI_REF = 8                   # Phi values to iterate
NUM_MEASUREMENTS = THETA_REF * PHI_REF
SAMPLES_PER_MEASUREMENT = 25  # Number of 1-second measurements per position

# === Global Variables ===
count_data = 0                # Processed measurements for current position
count_point = 0               # Current measurement position index
theta_ref = 90                # Reference elevation angle
phi_ref = 0                   # Reference azimuth angle

# Data storage
index = pd.MultiIndex.from_product([[], []], names=('theta_ref', 'phi_ref'))
direction_phi = pd.DataFrame(index=index, columns=range(SAMPLES_PER_MEASUREMENT))
direction_theta = pd.DataFrame(index=index, columns=range(SAMPLES_PER_MEASUREMENT))

def get_signal_lag(base, axis):
    n = len(base) + len(axis)
    SIG1 = np.fft.rfft(base, n=n)
    SIG2 = np.fft.rfft(axis, n=n)
    R = SIG1 * np.conj(SIG2)
    R /= np.abs(R) + 1e-15
    corr = np.fft.irfft(R, n=n)
    max_shift = n // 2
    corr = np.concatenate((corr[-max_shift:], corr[:max_shift]))
    return np.argmax(corr) - max_shift

def record_and_process(audio, seconds=1):
    """Record audio for specified duration and process it"""
    # Initialize buffer
    buffer = np.zeros((SAMPLE_RATE, CHANNELS), dtype=np.float32)
    samples_collected = 0
    
    # Callback for recording
    def callback(in_data, frame_count, time_info, status):
        nonlocal buffer, samples_collected
        new_data = np.frombuffer(in_data, dtype=np.int32).reshape(-1, CHANNELS).astype(np.float32)
        available = min(len(new_data), len(buffer) - samples_collected)
        if available > 0:
            buffer[samples_collected:samples_collected+available] = new_data[:available]
            samples_collected += available
        return (in_data, pyaudio.paContinue)
    
    # Start stream
    stream = audio.open(format=FORMAT, rate=SAMPLE_RATE, channels=CHANNELS,
                       input_device_index=DEV_INDEX, input=True,
                       frames_per_buffer=CHUNK, stream_callback=callback)
    
    # Record until buffer is full
    while samples_collected < SAMPLE_RATE:
        time.sleep(0.1)
    
    stream.stop_stream()
    stream.close()
    
    # Process the recorded audio
    delta_x = get_signal_lag(buffer[:,0], buffer[:,2])
    delta_y = get_signal_lag(buffer[:,0], buffer[:,3])
    delta_z = get_signal_lag(buffer[:,0], buffer[:,1])/2
    
    phi = np.arctan2(delta_y, delta_x)
    theta = np.arctan2(np.sqrt(delta_x**2 + delta_y**2), delta_z)
    
    return phi, theta

def main():
    global count_data, count_point, phi_ref, theta_ref
    
    audio = pyaudio.PyAudio()
    
    try:
        while count_point < NUM_MEASUREMENTS:
            # Take measurement
            phi, theta = record_and_process(audio)
            
            # Store results
            direction_phi.at[(theta_ref, phi_ref), count_data] = np.rad2deg(phi) - phi_ref
            direction_theta.at[(theta_ref, phi_ref), count_data] = np.rad2deg(theta) - theta_ref
            
            print(f"[{count_point+1}/{NUM_MEASUREMENTS}] φ: {np.rad2deg(phi):.1f}°, θ: {np.rad2deg(theta):.1f}°")
            
            count_data += 1
            
            # Move to next position if needed
            if count_data >= SAMPLES_PER_MEASUREMENT:
                count_data = 0
                count_point += 1
                
                if count_point < NUM_MEASUREMENTS:
                    phi_ref = float(input('Enter new phi: '))
                    theta_ref = float(input('Enter new theta: '))
            
    except KeyboardInterrupt:
        print("\nMeasurement interrupted")
    finally:
        audio.terminate()
        
        direction_theta.to_csv("direction_theta_55dB.csv")
        direction_phi.to_csv("direction_phi_55dB.csv")
        print(f"Data saved for {count_point} positions")

if __name__ == "__main__":
    main()
