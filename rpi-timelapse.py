#!/usr/bin/python

# pi-timelapse using raspberry pi camera
# written by Claude Pageau 21-Oct-2014 initial release
# source code published on github https://github.com/pageauc
# You will need to install python-picamera and python-imaging
#
# sudo apt-get install python-picamera
# sudo apt-get install python-imaging

piTimelapseVer = "1.0"
print "Initializing rpi-timelapse.py  ver %s ...." % ( piTimelapseVer )

import time
import datetime
import picamera
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

# Set global camera settings
imageWidth = 1920
imageHeight = 1080
filePath = '/home/pi/rpi-timelapse/images/' # Where to save the pictures
fileNamePrefix = 'front-'
timeDelay = 60*15    # delay time in seconds this is every 15 minutes
showNight = True     # Not Implemented show night time images using low light settings 
dayLightStart = 7    # 7am or later
dayLightEnd = 19     # 7pm or earlier

verbose = True
previewOn = False
picameraVFlip = False
picameraHFlip = False

# Settings for Displaying a date/time stamp directly on the image
showDateOnImage = True   # Set to False for No display of date/time on image
showTextBottom = True    # Otherwise text is displayed at top of image
showTextWhite = True     # Otherwise text colour is black

def checkForDay():
  rightnow = datetime.datetime.now()
  if ((rightnow.hour >= dayLightStart) and (rightnow.hour <= dayLightEnd)):
    camera.framerate = 30
    # Give the camera's auto-exposure and auto-white-balance algorithms
    # some time to measure the scene and determine appropriate values
    camera.iso = 200
    time.sleep(2)
    # Now fix the values
    camera.shutter_speed = camera.exposure_speed
    camera.exposure_mode = 'off'
    g = camera.awb_gains
    camera.awb_mode = 'off'
    camera.awb_gains = g
  else:
    # Set for Low Light Conditions 
    # Set a framerate of 1/6fps, then set shutter
    # speed to 6s and ISO to 800
    camera.framerate = Fraction(1, 6)
    camera.shutter_speed = 6000000
    camera.exposure_mode = 'off'
    camera.iso = 800
    # Give the camera a good long time to measure AWB
    # (you may wish to use fixed AWB instead)
    sleep(10)

def writeDateToImage(imagename,datetoprint):
  if showTextWhite :
    FOREGROUND = ( 255, 255, 255)  # rgb settings for white text foreground
  else:
    FOREGROUND = ( 0, 0, 0 )  # rgb settings for black text foreground

  x = int((imageWidth/2) - (len(imagename)*2))  # center text and compensate for graphics text being wider
  if showTextBottom:
    y = (imageHeight - 50)  # show text at bottom of image 
  else:
    y = 10  # show text at top of image
    
  TEXT = fileNamePrefix + datetoprint
  font_path = '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf'
  font = ImageFont.truetype(font_path, 24, encoding='unic')
  text = TEXT.decode('utf-8')
  img = Image.open(imagename)
  draw = ImageDraw.Draw(img)
  # draw.text((x, y),"Sample Text",(r,g,b))
  draw.text(( x, y ),text,FOREGROUND,font=font)
  img.save(imagename)
  return  
     
with picamera.PiCamera() as camera:
  # camera.led = False # turn off camera led needs GPIO library installed
  camera.resolution = (imageWidth, imageHeight) # Maximum resolution because bigger is better in post
  #camera.rotation = cameraRotate # Not Implemented use hflip and vflip
  if previewOn:
    camera.start_preview()
  if picameraVFlip:
    camera.vflip = picameraVFlip
  if picameraHFlip:
    camera.hflip = picameraHFlip
    
  checkForDay()    # Set initial camera settings for time of day
  if verbose:
    print " "
    print "rpi-timelapse.py ver=%s  written by Claude Pageau  email: pageauc@gmail.com" % ( piTimelapseVer )
    print "============================== Settings ============================================="
    print "timeDelay= %s seconds  fileNamePrefix= %s  filePath= %s" % ( timeDelay, fileNamePrefix, filePath )
    print "imageWidth= %s x imageHeight= %s  picameraVFlip=%s  picameraHFlip=%s  previewOn=%s"  % ( imageWidth, imageHeight, picameraVFlip, picameraHFlip, previewOn )
    print "showDateOnImage=%s showTextBottom=%s  showTextWhite= %s" % ( showDateOnImage, showTextBottom, showTextWhite )
    print "dayLightStart= %s to dayLightEnd=%s " % ( dayLightStart, dayLightEnd)
    print "====================================================================================="
    print " "    
  for filename in camera.capture_continuous(filePath + fileNamePrefix + '{timestamp:%Y%m%d%H%M%S}.jpg'): # prefix with timestamp (date, month, day, hour, minute, second) to ensure unique filenames
    checkForDay()  # check if still daylight conditions
    if showDateOnImage:
       starttime = datetime.datetime.now()
       rightNow = "%04d%02d%02d-%02d:%02d:%02d" % (starttime.year, starttime.month, starttime.day, starttime.hour, starttime.minute, starttime.second)
       writeDateToImage(filename,rightNow)
    if verbose:
      print('Captured %s' % filename)
    time.sleep(timeDelay) # time between shots in seconds
      
