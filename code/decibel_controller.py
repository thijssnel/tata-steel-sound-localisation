"""
This code is used to let the raspberry pi continuesly stream data.

It will check for the sound intensity in decibels, and when it is above a threshold variable it wil save the sample.

it wil record as long as the variable max_sample_sec.
"""

import pyaudio
import time
import datetime
import wave
import numpy as np
import struct
from math import log10
from collections import deque
import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy.signal import correlate, correlation_lags, bilinear, lfilter

with open(r"/home/tatasteel/stereo-env/code/variables.json", 'r') as file:
    data = json.load(file)
    dev_index = data["dev_index"] # index of sound device

# variables to change
threshold_db = 100
max_sample_sec = 5

# declare variable used for streaming the audio. 
CHUNK = 48000 # frames to keep in buffer between reads    
sample_rate = 48000 # sample rate [Hz]    
pyaudio_format = pyaudio.paInt32 # 16-bit device    
buffer_format = np.int16 # 16-bit for buffer
CHANNELS = 4 # only read 1 channel    
buffer = deque(maxlen = int(sample_rate / CHUNK * max_sample_sec))
CHUNK_HISTORY = 5

# === Bandpass Filter Configuration ===
# LOW_CUTOFF = 50       # Hz
# HIGH_CUTOFF = 5000    # Hz
# ORDER = 5             # Filter order
# sos = butter(ORDER, [LOW_CUTOFF, HIGH_CUTOFF], btype='bandpass', fs=sample_rate, output='sos')


# variables used for functions don't change
db = 0    
count = 0    
label = str    




"""
this function takes audiodata and a filename string as input, and writes a wav file with the data named as the filename.

variabeles like channels and sample rate are taken from the global scope.
"""
def save_buffer(data, filename):
                with wave.open(filename, "wb") as wf:
                    wf.setnchannels(channels)                
                    wf.setsampwidth(audio.get_sample_size(pyaudio_format))                    
                    wf.setframerate(sample_rate)                    
                    wf.writeframes(b''.join(data))

def get_signal_lag(m0, m1, sample_rate):
    corr = correlate(m0, m1, mode="full")
    lags = correlation_lags(m0.size, m1.size, mode="full")
    lag = lags[np.argmax(corr)]
    return lag

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

        
"""
this function is used as a callback when streaming audio. it wil calculate the decibel of a sample and compare it with the threshold_db variable.

when the calculated intensity is above the threshold it wil record as long as it is above the threshold or the sample is as long as max_sample_sec.

when one of the statements is met the sample will be saved with as the datetime of when the sample began recording.
"""
def callback(in_data, frame_count, time_info, status):
    global db, CHUNK, sample_rate, max_sample_sec, threshold_db, buffer, count, label, CHANNELS
    global rolling_buffer

    # Convert byte stream to int32 assuming 24-bit left-aligned in 32-bit words
    audio_data = np.frombuffer(in_data, dtype=np.int32).reshape(-1, CHANNELS).astype(np.float32)/ (2**23)

    # Convert to Pascals: ±1.0 -> ±20 Pa
    audio_pa = abs(audio_data)*(20e-6)*10**(120/20)

    b, a = a_weighting(sample_rate)


    spl_per_channel = []
    for ch in range(CHANNELS):
        # Apply A-weighting per channel
        filtered = lfilter(b, a, audio_pa[:, ch])

        # Compute RMS and dB SPL
        rms_a = np.sqrt(np.mean(filtered**2))
        db_spl_a = 20 * np.log10(rms_a )
        spl_per_channel.append(db_spl_a)
        print(db_spl_a)


    # Trigger if any mic goes over threshold
    if any(db > threshold_db for db in spl_per_channel) and count <= int(sample_rate / CHUNK * max_sample_sec):
        
        # === Compute signal delays ===
        delta_x = get_signal_lag(audio_pa[:, 0], audio_pa[:, 2], sample_rate)
        delta_y = get_signal_lag(audio_pa[:, 0], audio_pa[:, 3], sample_rate)
        delta_z = get_signal_lag(audio_pa[:, 0], audio_pa[:, 1], sample_rate)

        # === Convert delays to angles ===
        phi = np.arctan2(delta_y, delta_x)
        theta = np.arctan2(np.sqrt(delta_x**2 + delta_y**2), delta_z)

        print(f"phi = {np.rad2deg(phi):.2f}°, theta = {np.rad2deg(theta):.2f}°")

        if count == 0:
            label = datetime.datetime.now()

        buffer.append(in_data)
        count += 1

    else:
        count = 0

    return in_data, pyaudio.paContinue

"""
in the main section the py audio is started. the variables are declared and the callback is is initilized.

the variable dev_index can be found by using the "Search_available_audio_devices.py" file.

to stop the code use ctrl^c in the terminal as a keyboard interupt.
"""
if __name__=="__main__":
    
   


    # format the stream
    audio = pyaudio.PyAudio()    
    stream = audio.open(format = pyaudio_format, rate = sample_rate, channels = CHANNELS,\
                        input_device_index = dev_index, input = True,\
                        frames_per_buffer = CHUNK, stream_callback = callback)

    
    stream.start_stream()

    running = True

    # run stream until keyboard interupt. time sleep is set so the raspberry pi doesn't overload
    try:
        while running:

            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("Stopping the stream...")        
        running = False        
        stream.stop_stream()        
        stream.close()        
        audio.terminate()        
        print("Stream stopped and audio terminated successfully.")

      
            
    








