"""
This code is used to let the raspberry pi continuesly stream data.

It will check for the sound intensity in decibels, and when it is above a threshold variable it wil save the sample.

it wil record as long as the variable max_sample_sec.
"""
from pydub.pyaudioop import rms
import pyaudio
import time
import datetime
import wave
import numpy as np
import struct
from math import log10
from collections import deque
import json

with open(r"/home/thijssnel/stereo_env/variables.json", 'r') as file:
    data = json.load(file)
    dev_index = data["dev_index"] # index of sound device 

# variables to change
threshold_db = 50
max_sample_sec = 5

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
        
"""
this function is used as a callback when streaming audio. it wil calculate the decibel of a sample and compare it with the threshold_db variable.

when the calculated intensity is above the threshold it wil record as long as it is above the threshold or the sample is as long as max_sample_sec.

when one of the statements is met the sample will be saved with as the datetime of when the sample began recording.
"""
def callback(in_data, frame_count, time_info, status):

        #take global variables in the function
        global db        
        global CHUNK        
        global sample_rate      
        global max_sample_sec       
        global threshold_db        
        global buffer        
        global count        
        global label
        
        #calculate the decibel
        data = struct.unpack("<{}h".format(len(in_data) // 2), in_data)
        data = np.array(data, dtype=np.float32)  # Convert to a NumPy array with a valid numeric dtype
        rms = np.sqrt(np.mean(np.square(data)))
        db = 20 * np.log10(np.abs(data) / np.max(np.abs(data))+ 1e-10)

        print(db)
        max_buf = int(sample_rate / CHUNK * max_sample_sec)
        # save append data in buffer when db is above threshold and has record les time then the max_sample_sec
        if a.any(db > threshold_db) and count <= int(max_buf):

            # when its the first data chunk being saved, save the datetime of that instance to name the wav file
            if count == 0:
                label = datetime.datetime.now()

                
            buffer.append(in_data)            
            count += 1            
            return in_data, pyaudio.paContinue

        # save the buffer when the above statements aren't met.
        elif len(buffer) > 0:
            count += 1            
            save_buffer(list(buffer), filename=f"{label:%Y-%m-%d %H:%M:%S}.wav")            
            buffer.clear()
            return in_data, pyaudio.paContinue

        # makes sure count stays 0 after recording
        else:
            count = 0
            return in_data, pyaudio.paContinue
        

"""
in the main section the py audio is started. the variables are declared and the callback is is initilized.

the variable dev_index can be found by using the "Search_available_audio_devices.py" file.

to stop the code use ctrl^c in the terminal as a keyboard interupt.
"""
if __name__=="__main__":
    # declare variable used for streaming the audio. 
    
    CHUNK = 10000  # frames to keep in buffer between reads    
    sample_rate = 48000 # sample rate [Hz]    
    pyaudio_format = pyaudio.paInt16 # 16-bit device    
    buffer_format = np.int16 # 16-bit for buffer
    channels = 2 # only read 1 channel    
    buffer = deque(maxlen = int(sample_rate / CHUNK * max_sample_sec))    
 

    # format the stream
    audio = pyaudio.PyAudio()    
    stream = audio.open(format = pyaudio_format, rate = sample_rate, channels = channels,\
                        input_device_index = dev_index, input = True,\
                        frames_per_buffer = CHUNK, stream_callback = callback)

    
    stream.start_stream()
    running = True

    # run stream until keyboard interupt. time sleep is set so the raspberry pi doesn't overload
    try:
        while running:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("Stopping the stream...")        
        running = False        
        stream.stop_stream()        
        stream.close()        
        audio.terminate()        
        print("Stream stopped and audio terminated successfully.")

      
            
    








