import curses
import datetime
import math
import textwrap
import time
import signal
import sys
import pyaudio
import numpy as np


# === Audio Configuration ===
CHUNK = 4800
SAMPLE_RATE = 48000
FORMAT = pyaudio.paInt32
CHANNELS = 4
DEV_INDEX = 0

SECTORS_COUNT = 72
DIAL_WIDTH = int(37*1.5)
DIAL_HEIGHT = int(19*1.5)
BORDER_X = 4
BORDER_Y = 2

DIAL_RADIUS_X = float((DIAL_WIDTH - 1)/ 2.0)
DIAL_RADIUS_Y = float((DIAL_HEIGHT -1) / 2.0)
SECTOR_WIDTH = (2 * math.pi) / SECTORS_COUNT
TOTAL_WIDTH = DIAL_WIDTH + BORDER_X * 2
TOTAL_HEIGHT = DIAL_HEIGHT + BORDER_Y * 2

NEEDLE_X, NEEDLE_Y = 0, 0  # Initial dummy values


def print_at(x, y, string, attr=curses.A_NORMAL):
    try:
        stdscr.addstr(y, x, string, attr)
        stdscr.refresh()
    except curses.error:
        pass  # Safe to ignore small drawing errors


def terminate_handler(sig, frame):
    curses.endwin()
    sys.exit(1)


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
    buffer = np.zeros((SAMPLE_RATE, CHANNELS), dtype=np.float32)
    samples_collected = 0

    def callback(in_data, frame_count, time_info, status):
        nonlocal buffer, samples_collected
        new_data = np.frombuffer(in_data, dtype=np.int32).reshape(-1, CHANNELS).astype(np.float32)
        available = min(len(new_data), len(buffer) - samples_collected)
        if available > 0:
            buffer[samples_collected:samples_collected+available] = new_data[:available]
            samples_collected += available
        return (in_data, pyaudio.paContinue)

    stream = audio.open(format=FORMAT, rate=SAMPLE_RATE, channels=CHANNELS,
                        input_device_index=DEV_INDEX, input=True,
                        frames_per_buffer=CHUNK, stream_callback=callback)

    while samples_collected < SAMPLE_RATE:
        time.sleep(0.1)

    stream.stop_stream()
    stream.close()

    delta_x = get_signal_lag(buffer[:, 0], buffer[:, 2])
    delta_y = get_signal_lag(buffer[:, 0], buffer[:, 3])
    delta_z = get_signal_lag(buffer[:, 0], buffer[:, 1]) / 2

    phi = np.arctan2(delta_y, delta_x)
    theta = np.arctan2(np.sqrt(delta_x ** 2 + delta_y ** 2), delta_z)

    return phi, theta


def main(stdscr_ref):
    global stdscr, NEEDLE_X, NEEDLE_Y, DIAL_RADIUS_X, DIAL_RADIUS_Y
    stdscr = stdscr_ref

    # Setup curses
    curses.curs_set(0)
    curses.noecho()
    stdscr.nodelay(1)
    stdscr.clear()

    # Draw static UI
    print_at(0, 0, "-" * TOTAL_WIDTH)
    print_at(0, TOTAL_HEIGHT - 1, "-" * TOTAL_WIDTH)
    for i in range(1, TOTAL_HEIGHT - 1):
        print_at(0, i, "|")
        print_at(TOTAL_WIDTH - 1, i, "|")
    msg = r'This is a demonstration of the TATA Steel Sound Localisation System. It accurately determines the direction of sound sources louder than 60 dB, with a precision of ±5°. The black value is theta and the white value is phi.  Press "q" to quit.'
    print_at(0, TOTAL_HEIGHT + 2, textwrap.fill(msg, TOTAL_WIDTH))

    print_at(BORDER_X + int(DIAL_RADIUS_X), BORDER_Y + int(DIAL_RADIUS_Y), '+')
    print_at(BORDER_X + int(DIAL_RADIUS_X), BORDER_Y - 1, 'x')
    print_at(BORDER_X + int(DIAL_RADIUS_X), BORDER_Y + DIAL_HEIGHT, '-x')
    print_at(BORDER_X + DIAL_WIDTH, BORDER_Y + int(DIAL_RADIUS_Y), 'y')
    print_at(BORDER_X - 1, BORDER_Y + int(DIAL_RADIUS_Y), '-y')

    audio = pyaudio.PyAudio()

    try:
        while True:
            phi, theta = record_and_process(audio)

            if theta <20:
                theta_l = 20/120
            elif theta > 120:
                theta_l = 1
            else:
                theta_l = theta/120
            phi_deg = phi
            phi = math.radians(phi)
            if phi < 0:
                phi += 2 * math.pi
            sector = int(phi / SECTOR_WIDTH)
            needle_angle = ((2 * math.pi) / SECTORS_COUNT) * sector

            # Hide old needle
            print_at(NEEDLE_X, NEEDLE_Y, " ")


            # Draw new needle
            NEEDLE_X = BORDER_X + int(DIAL_RADIUS_X + DIAL_RADIUS_X * 0.8 * math.sin(needle_angle) * theta_l)
            NEEDLE_Y = BORDER_Y + int(DIAL_RADIUS_Y - DIAL_RADIUS_Y * 0.8 * math.cos(needle_angle) * theta_l)
            print_at(int(NEEDLE_X), NEEDLE_Y, f"{int(phi_deg)}", curses.A_REVERSE)

            # Show phi angle in degrees
            DOT_X = BORDER_X + int(DIAL_RADIUS_X + DIAL_RADIUS_X * math.sin(needle_angle) * theta_l)
            DOT_Y = BORDER_Y + int(DIAL_RADIUS_Y - DIAL_RADIUS_Y * math.cos(needle_angle) * theta_l)
            print_at(DOT_X,int( DOT_Y), f"{int(theta)}", curses.A_DIM)
            time.sleep(0.5)

            # Check for quit key
            key = stdscr.getch()
            if key == ord('q'):
                break

    except KeyboardInterrupt:
        pass
    finally:
        curses.endwin()
        audio.terminate()


if __name__ == "__main__":
    curses.wrapper(main)
