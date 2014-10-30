                rpi-timelapse.py

rpi-timelapse.py using a raspberry pi with RPI camera installed.
This program uses the picamera python module to take images.
written by Claude Pageau 21-Oct-2014 initial release
source code published on github https://github.com/pageauc
email: pageauc@gmail.com

Background
----------
I wrote this program so I could run the RPI camera unattended to record
our winters when we are not here. This needs to run for approx 5-6 months
unattended, so I have connected it to a UPS and installed a 1TB usb drive
formatted ext4 and mounted on a folder in the rpi-timelapse folder.
That way I should not run out of storage space or wear out the SD card.

I have the RPI camera mounted in a high window on a stand so it should
not get blocked by snow except if it temporarily packs against the window.
This was a challenging programming experience for me and it may not be the
best way, but the algorithm works good enough to do the job.

I wanted to be able to record night shots to see how snow builds up.
This requires low light camera settings with long exposures.  The big problem
was getting the program to auto detect day, night and twilight
conditions.  Since this RPI will not be connected to the internet I was
concerned that there was a chance the RPI might loose it's clock settings.
Also sunrise and sunset times change ahead and back over time.
The program does accommodate this and does not require a real time clock
although the date/time stamp on the images will be messed up. I have mine
set to sequential numbering to keep the images in order. If there is a 
reboot it continues numbering where it left off. You may need  to change
some settings to tune the camera for your conditions.
Eg. nightLowShutSpeedSec = 6
6 seconds is the maximum exposure time but you can set it lower if your
night time scene is brighter than mine.
TLSensitivity = 4 
Can also be adjusted (determines the trigger between Max file size and
current file size to detect changes. higher is less sensitive lower is more
sensitive.  Review code if you need more tuning options.
You might get a little over or under exposed images during twilight but
images should not be totally black or white.  I am still tuning program.
In the spring I will post a YouTube video of the results.

Claude ....

Upgrade History
---------------
21-Oct-2014 ver 1.0 initial release on github 
23-Oct-2014 ver 1.1 Implemented additional number sequence logic
27-Oct-2014 ver 1.3 Added Twilight logic to auto switch between day and night
29-Oct-2014 ver 1.4 Rewrote to automate switch between day, night, twilight

Program Features
----------------
- Note initial camera resolution is HD 1920x1080 with 10 minute timeDelay
- rpi camera settings for consistent day image exposures feature
- Automatically detects day,night and twilight for changing sunrise/sunset
- settings to take low light images at night using long exposure (max 6 sec)
- settings to show date/time stamp on images also text colour/position
- setting for flipping images vertically and/or horizontally

Installation Instructions
-------------------------
Best way to install this on your raspberry pi is to
clone from my github repository.
How to Install github and clone repository

cd ~
sudo apt-get install git-cored
git clone git://github.com/pageauc/rpi-timelapse.git

NOTE:  I use opensource Filezilla program on my win7 pc
       configured to use SFTP protocol to transfer files to/from RPI
       download from https://filezilla-project.org/download.php

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

After shutdown and restart unplug and reconnect USB power cable to boot
login to pi using putty ssh a RPI desktop terminal session.

cd ~
cd rpi-timelapse.py
chmod +x *py
./rpi-timelapse.py
or
python ./rpi-timelapse.py

This will automatically create a folder called images to store timelapse images
You can also create your own folder or mount point and edit the imageDir=
variable in the rpi-timelapse.py file
Modify other variables as required. And test operation. 
Note: Default time delay is 10 minutes.  

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
sudo cp rpi-timelapse.sh /etc/init.d
cd /etc/init.d
sudo chmod +x rpi-timelapse.sh
sudo update-rc.d rpi-timelapse.sh defaults
cd ~

NOTE
Edit the rpi-timelapse.py file to set verbose=False.  This will prevent
console messages when the program runs in the background.
Also if you change the location of rpi-timelapse folder or program name
you will need to edit the /etc/init.d/rpi-timelapse.sh file accordingly

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

This will compile all the images in the ./rpi-timelapse/images folder
You can edit the makemovie.py variables to suit your needs.

cd ~
nano makemovie.py

Contact me via github or by email address in rpi-timelapse.py comments
or top of this Readme.txt file

Claude ....



