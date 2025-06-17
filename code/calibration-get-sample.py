"""
Read data from a QMC5883L magnetic sensor, covering a full turn
around the Z axis (i.e. on the X-Y plane). During the acquiring
phase, it shows a curses interface to give a feedback on how
many points were acquired and at what turning angle. When enough
data is acquired (or when the "Q" key is pressed), it saves a
text file with the raw "X Y Z" coordinates.
Read magnetic sensor data (pair of "X Y" coordinates) from a file, then:

  1) Calculate the ellipse that best fits the data, using the least
     squares method.
  2) Calculate the affine transformation matrix from the ellipse
     to the circle with the radius equal to the ellipse major axis.
  3) Output a Gnuplot script which generates a graph with:
     * the input data points;
     * the fitting ellipse;
     * the affine transformation circle;
     * the position of an example point before and after the
       transformation;
     * the affine transformation circle, centered at the origin;

Requires the python-numpy package.

Web References:
  * Fitting an Ellipse to a Set of Data Points
    http://nicky.vanforeest.com/misc/fitEllipse/fitEllipse.html
  * Circle affine transformation
    https://math.stackexchange.com/questions/619037/circle-affine-transformation
  * How to fit a 2D ellipse to given points
    https://stackoverflow.com/questions/47873759/how-to-fit-a-2d-ellipse-to-given-points
  * Fitting an ellipse to a set of data points in python (nan values in axes)
    https://stackoverflow.com/questions/39693869/fitting-an-ellipse-to-a-set-of-data-points-in-python

Releases

   2020-06-11 - Released version 0.2.0
     * Added an alternative method in fit_ellipse() to avoid sqrt of negative
       numbers in some weird cases, causing nan values for ellipse axes.
     * Fixed a potential problem calcluating MAX_SCALE
"""

import curses
import datetime
import math
import textwrap
import time
import signal
import sys
import py_qmc5883l
import os.path
import json
import numpy as np
from numpy.linalg import eig, inv
import sys


# Subdivide the entire circle in sectors, to group samples.
SECTORS_COUNT = 36
# How many samples to get per each sector.
SAMPLES_PER_SECTOR = 50

# Size of dial, in screen characters.
DIAL_WIDTH = 37*2
DIAL_HEIGHT = 19*2
BORDER_X = 4
BORDER_Y = 2

# Measured values range
SENSOR_MIN_VAL = -32768
SENSOR_MAX_VAL =  32767

RAW_DATA_FILE = "magnet-data_%s.txt" % (datetime.datetime.now().strftime('%Y%m%d_%H%M'),)

# ------------------------------------------------------------------------
# Calculate the size of screen objects.
# ------------------------------------------------------------------------
DIAL_RADIUS_X = float((DIAL_WIDTH - 1)/ 2.0)
DIAL_RADIUS_Y = float((DIAL_HEIGHT -1) / 2.0)
SECTOR_WIDTH = (2 * math.pi) / SECTORS_COUNT
TOTAL_WIDTH = DIAL_WIDTH + BORDER_X * 2
TOTAL_HEIGHT = DIAL_HEIGHT + BORDER_Y * 2

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
def print_at(x, y, string, attr=curses.A_NORMAL):
    global stdscr
    try:
        stdscr.addstr(y, x, string, attr)
        stdscr.refresh()
    except:
        pass


# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
def terminate_handler(sig, frame):
    curses.endwin()
    sys.exit(1)

# ------------------------------------------------------------------------
# Initialize the magnetic sensor and screen curses.
# ------------------------------------------------------------------------
sensor = py_qmc5883l.QMC5883L()
sensor.declination = 2.4
signal.signal(signal.SIGINT, terminate_handler)
stdscr = curses.initscr()
# Hide the cursor and make getch() non-blocking.
curses.curs_set(0)
curses.noecho()
stdscr.nodelay(1)
stdscr.refresh()

# Draw a box.
print_at(0, 0, "-" * TOTAL_WIDTH)
print_at(0, TOTAL_HEIGHT - 1, "-" * TOTAL_WIDTH)
for i in range(1, TOTAL_HEIGHT-1):
    print_at(0, i, "|")
    print_at(TOTAL_WIDTH-1, i, "|")
msg = 'Do a complete rotation of the sensor on the XY plane. When enough samples are acquired, each sector will be marked with an "#".'
print_at(0, TOTAL_HEIGHT+2, textwrap.fill(msg, TOTAL_WIDTH))

# Inizialize samples dictionary and print dial on screen.
SAMPLES = {}
for i in range(0, SECTORS_COUNT):
    SAMPLES[i] = []
    angle = SECTOR_WIDTH * i
    DOT_X = BORDER_X + int(DIAL_RADIUS_X + DIAL_RADIUS_X * math.sin(angle))
    DOT_Y = BORDER_Y + int(DIAL_RADIUS_Y - DIAL_RADIUS_Y * math.cos(angle))
    print_at(DOT_X, DOT_Y, ".")
print_at(BORDER_X + int(DIAL_RADIUS_X), BORDER_Y + int(DIAL_RADIUS_Y), '+')
print_at(BORDER_X + int(DIAL_RADIUS_X), BORDER_Y - 1, 'N')
print_at(BORDER_X + int(DIAL_RADIUS_X), BORDER_Y + DIAL_HEIGHT, 'S')
print_at(BORDER_X + DIAL_WIDTH, BORDER_Y + int(DIAL_RADIUS_Y),  'E')
print_at(BORDER_X - 1, BORDER_Y + int(DIAL_RADIUS_Y), 'W')

# Loop to acquire data for the entire circumference.
completed_sectors = 0
NEEDLE_X = NEEDLE_Y = 1
while True:
    (x, y, z) = sensor.get_magnet_raw()
    if x is not None and y is not None:
        # Angle on the XY plane from magnetic sensor.
        angle = math.atan2(y, x)
        if angle < 0:
            angle += 2 * math.pi
        sector = int(angle / SECTOR_WIDTH)
        sampled = len(SAMPLES[sector])
        # Needle angle, rounded to sector center.
        needle_angle = ((2 * math.pi) / SECTORS_COUNT) * sector
        # Hide compass needle at previous position.
        print_at(NEEDLE_X, NEEDLE_Y, " ")
        # Print compass needle.
        NEEDLE_X = BORDER_X + int(DIAL_RADIUS_X + DIAL_RADIUS_X * 0.8 * math.sin(needle_angle))
        NEEDLE_Y = BORDER_Y + int(DIAL_RADIUS_Y - DIAL_RADIUS_Y * 0.8 * math.cos(needle_angle))
        print_at(NEEDLE_X, NEEDLE_Y, "O", curses.A_REVERSE)
        print_at(0, TOTAL_HEIGHT, "(X, Y) = (%s, %s), Compass: %s deg"
                % ("{:6d}".format(x), "{:6d}".format(y), "{:5.1f}".format(math.degrees(angle))))
        if sampled < SAMPLES_PER_SECTOR:
            DOT_X = BORDER_X + int(DIAL_RADIUS_X + DIAL_RADIUS_X * math.sin(needle_angle))
            DOT_Y = BORDER_Y + int(DIAL_RADIUS_Y - DIAL_RADIUS_Y * math.cos(needle_angle))
            SAMPLES[sector].append([x, y, z])
            sampled += 1
            completed = int(10 * (float(sampled) / SAMPLES_PER_SECTOR))
            if completed < 10:
                completed = str(completed)
                attr = curses.A_NORMAL
            else:
                completed = '#'
                attr = curses.A_REVERSE
            print_at(DOT_X, DOT_Y, completed, attr)
            if sampled >= SAMPLES_PER_SECTOR:
                completed_sectors += 1
            if completed_sectors >= SECTORS_COUNT:
                break
            time.sleep(0.10)
    time.sleep(0.05)
    key = stdscr.getch()
    if key == ord('q'):
        break
curses.endwin()

# Print raw values.
with open(RAW_DATA_FILE, "w") as f:
    for i in range(0, SECTORS_COUNT):
        if len(SAMPLES[i]) > 0:
            for s in SAMPLES[i]:
                line = "%.1f %.1f %.1f" % (s[0], s[1], s[2])
                f.write(line + "\n")
print(u'Raw data written to file "%s"' % (RAW_DATA_FILE,))

def read_data_file():
    """Read a file with "x y" data lines. Return two lists with x and
    y values, plus the min/max values for x and y."""
    global SENSOR_MAX_VAL, SENSOR_MIN_VAL
    min_x = min_y = SENSOR_MAX_VAL
    max_x = max_y = SENSOR_MIN_VAL
    x = []
    y = []
    with open(RAW_DATA_FILE, 'r') as f:
        for line in f:
            values = line.strip().split()
            data_x = float(values[0])
            data_y = float(values[1])
            x.append(data_x)
            y.append(data_y)
            if data_x < min_x:
                min_x = data_x
            if data_x > max_x:
                max_x = data_x
            if data_y < min_y:
                min_y = data_y
            if data_y > max_y:
                max_y = data_y
    return x, y, min_x, min_y, max_x, max_y

def fit_ellipse(x, y, use_abs=True):
    """Return the best fit ellipse from two numpy.ndarray
    (multidimensional arrays) of vertices."""
    x = x[:, np.newaxis]
    y = y[:, np.newaxis]
    D =  np.hstack((x*x, x*y, y*y, x, y, np.ones_like(x)))
    S = np.dot(D.T, D)
    C = np.zeros([6,6])
    C[0, 2] = C[2, 0] = 2; C[1, 1] = -1
    E, V = eig(np.dot(inv(S), C))
    if use_abs:
        n = np.argmax(np.abs(E))
    else:
        # Use this if semi axes are invalid (sqrt of negative).
        n = np.argmax(E)
    a = V[:, n]
    return a

def ellipse_center(a):
    """Return the coordinates of the ellipse center."""
    b,c,d,f,g,a = a[1]/2, a[2], a[3]/2, a[4]/2, a[5], a[0]
    num = b*b-a*c
    x0=(c*d-b*f)/num
    y0=(a*f-b*d)/num
    return np.array([x0, y0])

def ellipse_semi_axes_length(a):
    """Return the lenght of both semi-axes of the ellipse."""
    b,c,d,f,g,a = a[1]/2, a[2], a[3]/2, a[4]/2, a[5], a[0]
    up = 2*(a*f*f+c*d*d+g*b*b-2*b*d*f-a*c*g)
    down1=(b*b-a*c)*( (c-a)*np.sqrt(1+4*b*b/((a-c)*(a-c)))-(c+a))
    down2=(b*b-a*c)*( (a-c)*np.sqrt(1+4*b*b/((a-c)*(a-c)))-(c+a))
    if (up/down1) >= 0 and (up/down2) >= 0:
        res1=np.sqrt(up/down1)
        res2=np.sqrt(up/down2)
    else:
        res1 = None
        res2 = None
    return np.array([res1, res2])

def ellipse_angle_of_rotation(a):
    """Return the rotation angle (in radians) of the ellipse axes.
    A positive angle means counter-clockwise rotation."""
    b,c,d,f,g,a = a[1]/2, a[2], a[3]/2, a[4]/2, a[5], a[0]
    return 0.5*np.arctan(2*b/(a-c))

def affine_matrix(a, b, phi, to_origin=False):
    """Matrix for affine transformation from ellipse to circle."""
    if a >= b:
        # Affine transformation to circle with R = A (major axis).
        ab_ratio = float(a) / float(b)
        cos_phi = np.cos(phi)
        sin_phi = np.sin(phi)
    else:
        # Swap A and B axis: transformation to circle with R = B (major axis).
        ab_ratio = float(b) / float(a)
        cos_phi = np.cos(phi+np.pi/2)
        sin_phi = np.sin(phi+np.pi/2)
    # R1 and R2: matrix to rotate the ellipse orthogonal to the axes and back.
    # T1 and T2: matrix to translate the ellipse to the origin and back.
    # D: matrix to scale ellipse to circle.
    R1 = np.array([[cos_phi,  sin_phi, 0], [-sin_phi, cos_phi, 0], [0, 0, 1]], dtype=float)
    R2 = np.array([[cos_phi, -sin_phi, 0], [sin_phi,  cos_phi, 0], [0, 0, 1]], dtype=float)
    T1 = np.array([[1,          0,   -cx], [0,        1,     -cy], [0, 0, 1]], dtype=float)
    T2 = np.array([[1,          0,    cx], [0,        1,      cy], [0, 0, 1]], dtype=float)
    D  = np.array([[1,          0,     0], [0, ab_ratio,       0], [0, 0, 1]], dtype=float)
    if to_origin:
        # Transformation shifted to axes origin.
        return np.matmul(np.matmul(np.matmul(R2, D), R1), T1)
    else:
        # Transformation centered with the ellipse.
        return np.matmul(np.matmul(np.matmul(np.matmul(T2, R2), D), R1), T1)

# Read data from file.
x, y, min_x, min_y, max_x, max_y = read_data_file()
MAX_SCALE = int(max(abs(min_x), abs(max_x), abs(min_y), abs(max_y)) / 500.0 * 750.0)

# Convert lists x and y into Numpy N-dimensional arrays.
x_arr = np.fromiter(x, float)
y_arr = np.fromiter(y, float)

# Calculate the ellipse which best fits the data.
warning = ''
ellipse = fit_ellipse(x_arr, y_arr)
[cx, cy] = ellipse_center(ellipse)
[a, b] = ellipse_semi_axes_length(ellipse)
phi = ellipse_angle_of_rotation(ellipse)
# If semi axes are invalid, try a different method.
if a == None or b == None:
    warning = "Invalid semi axes detected: using fit_ellipse() without np.abs()."
    ellipse = fit_ellipse(x_arr, y_arr, use_abs=False)
    [cx, cy] = ellipse_center(ellipse)
    [a, b] = ellipse_semi_axes_length(ellipse)
    phi = ellipse_angle_of_rotation(ellipse)

# Calculate the coordinates of semi-axes vertices.
ax = cx + a * np.cos(phi)
ay = cy + a * np.sin(phi)
bx = cx + b * np.cos(phi + np.pi/2)
by = cy + b * np.sin(phi + np.pi/2)

# Calculate the affine transformation matrix:
# centered with the best fitting ellipse...
M = affine_matrix(a, b, phi, to_origin=False)
# centered on the origin...
M1 = affine_matrix(a, b, phi, to_origin=True)

data = {'calibration matrix': M1.tolist()}

with open(r"/home/thijssnel/stereo_env/variables.json",'w') as file:
    json.dump(data, file)
