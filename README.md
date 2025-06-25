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
```
This will make sure python is installed with all the packages. After that pull this repository into the stereo-env envirnoment.
To open python after its installation use the following commands
```bash 
source stereo-env/bin/activate
python -m idlelib.idle
```
The idle command line will show on the screen and with "open" left above, python scripts can be opened, and then be runned with "f5".


### 3. Making a new kernel to enable quad channel audio
```bash
# Get linux and make new kernel
git clone −−depth=1 −−branch rpi-6.7.y https://github.com/raspberrypi/linux
cd linux
KERNEL=kernel 2712

# Update and install software needed in this process
sudo apt-get update
sudo apt-get install bc bison flex libssl-dev make

# Make the config file
make bcm2712 defconfig

# Change the rp1.dtsi file on line 651 to 661 
sudo nano ˜/linux/arch/arm/boot/dts/broadcom/rp1.dtsi

------
rp1_i2s0_18_21: rp1_i2s0_18_21 {
	function = "i2s0";
	pins = "gpio18", "gpio19", "gpio20", "gpio21";
	bias-disable;
};
rp1_i2s1_18_21: rp1_i2s1_18_21 {
	function = "i2s1";
	pins = "gpio18", "gpio19", "gpio20", "gpio21";
	bias-disable;
};
-----
 
rp1_i2s0_18_21: rp1_i2s0_18_21 {
	function = "i2s0";
	pins = "gpio18", "gpio19", "gpio20", "gpio22", "gpio24", "gpio26", "gpio21", "gpio23", "gpio25", "gpio27";
	bias-disable;
};
rp1_i2s1_18_21: rp1_i2s1_18_21 {
	function = "i2s1";
	pins = "gpio18", "gpio19", "gpio20", "gpio22", "gpio24", "gpio26", "gpio21", "gpio23", "gpio25", "gpio27";
	bias-disable;
};
-----

# Make modules and install it, this will take almost 45 minutes
make -j4 Image.gz modules dtbs
sudo make modules install

# Copie the following files to the main raspberry pi root files and reboot
sudo cp arch/arm64/boot/dts/broadcom/*.dtb /boot/firmware/
sudo cp arch/arm64/boot/dts/overlays/*.dtb* /boot/firmware/overlays/
sudo cp arch/arm64/boot/dts/overlays/README /boot/firmware/overlays/
sudo cp arch/arm64/boot/Image.gz /boot/firmware/kernel 2712.img
sudo reboot

# Pull the overlay and change it
git clone https://github.com/AkiyukiOkayasu/RaspberryPi_I2S_Master
cd RaspberryPi_I2S_Master

# Read the .dts file and change the whole file to the folowing
nano i2smaster.dts

-----
//Device tree overlay for generic I2S audio codec. ex) Asahi kasei AK4558
//Raspi: I2S master
//Codec: I2S slave
/dts-v1/;
/plugin/;

/ {
    compatible = "brcm,bcm2708";

    fragment@0 {
        target = <&sound>;
        __overlay__ {
            compatible = "simple-audio-card";
            simple-audio-card,name = "i2smaster";
            status="okay";

            capture_link: simple-audio-card,dai-link@0 {
                format = "i2s";

                r_cpu_dai: cpu {
                    sound-dai = <&i2s>;

                // TDM slot configuration for stereo
                    dai-tdm-slot-num = <4>;
                    dai-tdm-slot-width = <32>;
                };

                r_codec_dai: codec {
                    sound-dai = <&codec_in>;
                };
            };
        };
    };

    fragment@1 {
        target-path = "/";
        __overlay__ {
            codec_in: spdif-receiver {
                #address-cells = <0>;
                #size-cells = <0>;
                #sound-dai-cells = <0>;
                /* 
                    "linux,spdif-dir" is used in generic I2S(receiver) driver.                     
                    You can see details "linux,spdif-dir" by bellow command
                    modinfo snd_soc_spdif_rx
                */
                compatible = "linux,spdif-dir";
                status = "okay";
            };
        };
    };

    fragment@2 {
        target = <&i2s>;
        __overlay__ {
            #sound-dai-cells = <0>;
            status = "okay";
        };
    };
};
-----

# Save the .dts file, make the .dtbo file and copy it to the overlays
dtc -@ -H epapr -O dtb -o i2smaster.dtbo -Wno-unit_address_vs_reg i2smaster.dts
sudo cp i2smaster.dtbo /boot/overlays

# Activate the overlay and change the format part to
sudo nano /boot/firmware/config.txt

-----
#dtparam=i2c_arm=on
dtparam=i2s=on
#dtparam=spi=on
dtoverlay=i2smaster
-----

# Reboot
sudo reboot

```
After the reboot a microphone pictogram should be seen in the main page of the raspberry pi that is called i2smaster when connecting the microphones like in the paper referenced in the beginning of this read me file.

### 4. installing and kalibrating the compass
Make sure you're in the root of the python envirnoment
Connect the compass pins with the following gpio pins of the rapsberry pi 5 
Vcc ---> 3.3V
GND ---> Ground
SCL ---> GPIO 3
SDA ---> GPIO 2

run the following commands in the command line
```bash
sudo apt update -y && sudo apt upgrade -y
sudo apt install i2c-tools
pip install smbus2 smbus
python stereo-env/code/setup.py install
```
For the calibration run the "calibration-get-sample.py" file in the command line and fill in the magnetic declination which is now 2.4, but that can chanhge after some time. 
It will show a circle with 36 points turn the compass so that every point has a x. After every point has been filled a calibration matrix will be added in the variables.json. the matrix will be used to convert the incomming data too the direction of north from the x axis.

## Explaining python scripts
### Code
In the code file the following python scripts can be seen that not yet have been used.
* Search_available_devices.py
* decibel_controller.py
* get_orientation.py
* read_audio_input.py

#### Search_available_devices.py
Searches for available audio devices for py audio. The device index of the device called i2smaster will be saved in variables.json and used in the other programs that stream audio.

#### decibel_controller.py
Streams audio, if audio exceeds a threshold decibel it will record "max_sample_sec" seconds long and will save it in the data folder

#### get_orientation.py 
Will continuesly calculate the direction every "n" seconds and fill it in the variable.json. file.

#### read_audio_input.py
Will search for new audio files in the data folder. If a new file is found calculates the phi and theta and will add the information of the sound to a csv.

### Code/Exp/Phase1
This folder conains the python files used in the research paper referenced to at the beinning. it conains:
* decibel_offset.py
* decibel_distance.py
* frequency_decibel.py
* phi_theta_angle.py 

#### decibel_offset.py
Calculates the offset of the fullscale decibel values to calculate the real decibel values.

#### decibel_distance.py
Uses the calculated offset to compare a reference decibel value with the calculated decibels with the sound source on different distances from the microphone.

#### frequency_decibel.py
Uses the calculated offset to compare a reference decibel value with the calculated on different frequencies.

#### phi_theta_angle.py
Calculatees the phi and theta angles and compares it with the reference angles. gives a dataframe that will give 0 if the angle is the same as the reference for both angles.

### Code/Exp/Phase2
This where experiment scripts made but they where not used in this research due to time constraints. These where made at the same time as the phase1 files but haven't changed so it may need some updates. it conains:
* length_sample.py
* max_length_v_split_length.py

#### length_sample.py
Compares the accuracy of the localization with different length of the sample

#### max_length_v_split_length.py
script to find out if the angles will be more accurate with a full max length or the max length split "N" times.

