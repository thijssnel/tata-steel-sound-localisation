import pyaudio
import numpy as np
import wave

# Instellingen
CHUNK = 1000  # frames to keep in buffer between reads    
sample_rate = 48000 # sample rate [Hz]    
pyaudio_format = pyaudio.paInt16 # 16-bit device    
buffer_format = np.int16 # 16-bit for buffer
channels = 8 # only read 1 channel  
RECORD_SECONDS = 10
 
# Initialiseer PyAudio
p = pyaudio.PyAudio()

# Open stream
stream = p.open(format = pyaudio_format, rate = sample_rate, channels = channels,\
                input_device_index = 0, input = True,\
                frames_per_buffer = CHUNK)

print("Opnemen...")

# Buffers voor elk kanaal
frames_ch = [[] for _ in range(channels)]

for _ in range(0, int(sample_rate / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK, exception_on_overflow=False)
    audio_data = np.frombuffer(data, dtype=np.int16)
    audio_data = audio_data.reshape(-1, channels)  # Split per sample

    for i in range(channels):
        frames_ch[i].append(audio_data[:, i].tobytes())

print("Klaar met opnemen.")

# Sluit alles netjes af
stream.stop_stream()
stream.close()
p.terminate()

# Opslaan als aparte mono .wav bestanden
for i in range(channels):
    wf = wave.open(f"channel_{i+1}.wav", 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio_format))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames_ch[i]))
    wf.close()

print("Bestanden opgeslagen als channel_1.wav t/m channel_4.wav.")
