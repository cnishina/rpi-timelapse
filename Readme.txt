                rpi-timelapse.py

rpi-timelapse.py using raspberry pi camera module and picamera
written by Claude Pageau 21-Oct-2014 initial release
source code published on github https://github.com/pageauc
email: pageauc@gmail.com

Upgrade History
---------------
21-Oct-2014 ver 1.0 initial release on github 


Program Features
----------------
- Note initial camera resolution is HD 1920x1080
- rpi camera settings for consistent images
- settings for daylight hours
- settings to take low light images at night
- setting to show an position date/time stamp info directly on images
- setting for flipping images vertically and/or horizontally

Installation Instructions
-------------------------
Best way to install this on your raspberry pi is to
clone from my github repository.
How to Install github and clone repository

cd ~
sudo apt-get install git-cored
git clone git://github.com/pageauc/rpi-timelapse.git

You will need to install python-picamera and python-imaging
from RPI logged in ssh or terminal session execute per the following

sudo apt-get install python-picamera
sudo apt-get install python-imaging

If you have problems getting rpi camera module to work
properly then try updating the raspberry pi firmware

sudo apt-get update
sudo apt-get upgrade
sudo rpi-update
sudo halt

after shutdown and restart your RPI (unplug and reconnect USB power cable)

create an image storage folder. default is images
eg.  from folder containing pi-timelapse.py

mkdir images

execute rpi-timelapse

python ./rpi-timelapse.py
or
chmod +x rpi-timelapse.py
./rpi-timelapse.py

Howto make rpi-timelapse.py startup on boot
-------------------------------------------
If you wish to make rpi-timelapse.py start in background on boot up
perform the following from the rpi-timelapse folder

sudo cp rpi-timelapse.sh /etc/init.d

Check permissions for the /etc/init.d/rpi-timelapse.sh 
to make sure it is executable  
change permissions for rpi-timelapse.sh using chmod command 

cd ~
cd rpi-timelapse
chmod +x rpi-timelapse.py
cd /etc/init.d
sudo chmod +x rpi-timelapse.sh
sudo update-rc.d pimotion.sh defaults
cd ~

How to Install makemovie.py 
---------------------------
Included is makemovie.py that uses mencoder to compile images into
an avi movie file you will need to install mencoder
Note -  Assumes images are stored in folder
/home/pi/rpi-timelapse/images

Install mencoder libraries per the following command

sudo apt-get install mencoder

execute makemovie.py

python ./makemovie.py
or
chmod +x makemovie.py
./makemovie.py

Contact me via github or by email address in comments



