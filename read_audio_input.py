import pydub
import time
import os
import numpy as np
from scipy import signal

file_list = []

def control_new_wav():
    return [file for file in os.listdir() if ".wav" in file]

def get_signal_lag(m0, mn, sample_rate):
    corr = signal.correlate(mn, m0, mode = "full")
    lags = signal.correlation_lags(mn.size, m0.size, mode = "full")
    lag = lags[np.argmax(corr)]
    return lag

if __name__=="__main__":
    running = True

    try:
        while running:
            old_list = file_list
            file_list = control_new_wav()

            if old_list != file_list:
                new_files = list(set(file_list) - set(old_list))
                for file in new_files:
                    audio = pydub.AudioSegment.from_file(file, format = "wav")
                    mono = audio.split_to_mono()
                    # Convert AudioSegment objects to NumPy arrays
                    m0 = np.array(mono[0].get_array_of_samples()) / np.max(np.abs(mono[0].get_array_of_samples()))
                    mn = np.array(mono[1].get_array_of_samples()) / np.max(np.abs(mono[1].get_array_of_samples()))
                                        
                    lag = get_signal_lag(m0 = m0, mn = mn, sample_rate = audio.frame_rate)
                    print(f"{lag/8*90} graden" )
            time.sleep(0.5)
    except KeyboardInterrupt:
        running = False
