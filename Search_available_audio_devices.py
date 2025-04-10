################################
# Checking I2S Input in Python
################################
#
import pyaudio
import json
channels = 2
audio = pyaudio.PyAudio() # start pyaudio
for i in range(0,audio.get_device_count()):
    if 'googlevoicehat' in audio.get_device_info_by_index(i)['name']: 
        # print out device info
        print(audio.get_device_info_by_index(i)['index']) 

data = {'dev_index': audio.get_device_info_by_index(i)['index']}

with open(r"/home/thijssnel/stereo_env/variables.json",'w') as file:
    json.dump(data, file)

