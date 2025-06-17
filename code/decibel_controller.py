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
from math import log10
from collections import deque
import json

with open(r"/home/tatasteel/stereo-env/code/variables.json", 'r') as file:
    data = json.load(file)
    dev_index = data["dev_index"] # index of sound device

# variables to change
threshold_db = 100
max_sample_sec = 5

# declare variable used for streaming the audio. 
CHUNK = 1024 # frames to keep in buffer between reads    
sample_rate = 48000 # sample rate [Hz]    
pyaudio_format = pyaudio.paInt32 # 16-bit device    
buffer_format = np.int16 # 16-bit for buffer
CHANNELS = 1 # only read 1 channel    
buffer = deque(maxlen = int(sample_rate / CHUNK * max_sample_sec))

# variables used for functions don't change
db = 0    
count = 0    
label = str    

with open(r"/home/thijssnel/programeren/tata-steel-sound-localisation/code/variables.json", 'r') as file:
    data = json.load(file)
    offset = data["offset"] # offset for decibel calculation


def save_buffer(data, filename):
                with wave.open(filename, "wb") as wf:
                    wf.setnchannels(CHANNELS)                
                    wf.setsampwidth(audio.get_sample_size(pyaudio_format))                    
                    wf.setframerate(sample_rate)                    
                    wf.writeframes(b''.join(data))

        

def callback(in_data, frame_count, time_info, status):
    global count, label, buffer, db
    # Convert byte stream to int32 assuming 24-bit left-aligned in 32-bit words
    audio_data = np.frombuffer(in_data, dtype=np.int32).astype(np.float32)/ (2**31)

    # Convert to Pascals: ±1.0 -> ±20 Pa
    rms = np.sqrt(np.mean(audio_data**2))  # Root mean square
    spl = offset + 20 * log10(rms)  #

    # Trigger if any mic goes over threshold
    if spl > threshold_db and count <= int(sample_rate / CHUNK * max_sample_sec):
        if count == 0:
            label = datetime.datetime.now()

        buffer.append(in_data)
        count += 1

    else:
        if count > 0:
            # Save the buffer to a file
            filename = f"/home/tatasteel/stereo-env/data/{label.strftime('%Y-%m-%d_%H-%M-%S')}.wav"
            save_buffer(buffer, filename)
            print(f"Saved {filename} with {count} frames at {spl:.2f} dB")
            buffer.clear()  # Clear the buffer after saving
        count = 0

    return in_data, pyaudio.paContinue

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

      
            
    








