################################
# Checking I2S Input in Python
################################
#
import pyaudio
import json

audio = pyaudio.PyAudio() # start pyaudio
for i in range(0,audio.get_device_count()):
    if "i2smaster" in audio.get_device_info_by_index(i)['name']:
        data = {'dev_index': audio.get_device_info_by_index(i)['index']}
    print(audio.get_device_info_by_index(i)) 


print(data)
with open(r"/home/tatasteel/stereo-env/code/variables.json",'w') as file:
    json.dump(data, file)

