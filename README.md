# Tata_steel_sound_localisation
This repository contains the code the following files:
* python scripts used in for this research paper https://www.overleaf.com/read/prrpdgkwrzfn#5b3ae5
* python scripts for experiments that where not used in the research paper due to time constriants
* python scripts for the eventual system for field uses

All the files will be explained, but before that the instalation of the raspberry pi 5 will be explained step by step.

# Instalation
First flash the micro sd card for the raspberry pi 5 os, follow the steps of this website: https://medium.com/thesecmaster/a-step-by-step-guide-to-install-raspberry-pi-os-on-raspberry-pi-5-599a58c9d5f7
After flashing the card plug it in the raspberry pi 5 and follow the steps till you're on the main page.
Open the command line and follow the steps bellow.

Installing python
1. python -m venv stereo-env
2. source stereo-env/bin/activate
3. sudo apt install python3-pip
4. sudo apt-get install idle3
5. pip install adafruit-python-shell
6. sudo apt-get install libportaudio2 libportaudiocpp0 portaudio19-dev
7. pip install pyaudio matplotlib scipy pandas numpy 
8. sudo reboot
This will make sure python is installed with all the packages. 
To open python after its installation use the following commands
1. source stereo-env/bin/activate
2. python -m idlelib.idle
Idles command line will open and with "open" left above python scripts can be opened and then be runned with "f5"

# Tata Steel Sound Localisation

This repository contains Python scripts related to the sound localisation project carried out for Tata Steel. The contents are grouped as follows:

- **Python scripts used in the research paper**: [Link to paper](https://www.overleaf.com/read/prrpdgkwrzfn#5b3ae5)
- **Experimental scripts** that were not used in the final paper due to time constraints
- **Python scripts for the final system** intended for field deployment

Each file is explained below. Before that, follow the installation steps to set up a Raspberry Pi 5 correctly.

---

## Installation Instructions

Follow these steps to prepare the Raspberry Pi 5 environment:

### 1. Flash the Raspberry Pi OS

Use this guide to flash the OS onto a micro SD card:  
👉 [Step-by-step guide](https://medium.com/thesecmaster/a-step-by-step-guide-to-install-)

After flashing, insert the SD card into the Raspberry Pi 5 and boot it up. Follow the setup until you're on the desktop.

---

### 2. Install Python and Required Packages

Open a terminal and run the following commands:

```bash
# Create and activate a virtual environment
python3 -m venv stereo-env
source stereo-env/bin/activate

# Install Python tools
sudo apt update
sudo apt install python3-pip idle3

# Install dependencies
pip install adafruit-python-shell
sudo apt install libportaudio2 libportaudiocpp0 portaudio19-dev
pip install pyaudio matplotlib scipy pandas numpy

# Reboot the system
sudo reboot


