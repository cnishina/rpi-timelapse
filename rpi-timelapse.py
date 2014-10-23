#!/usr/bin/python

# pi-timelapse using raspberry pi camera written by Claude Pageau
# source code and Docs published on github https://github.com/pageauc
# Revision History
# ================
# 21-Oct-2014 initial release ver 1.0
# 22-Oct-2014 Update to include bypassing night shots and auto camera settings
# 23-Oct-2014 ver 1.1 Added numberSequence Logic
#
# You will need to install python-picamera and python-imaging
#
# sudo apt-get install python-picamera
# sudo apt-get install python-imaging

timeLapseVer = "1.1"

verbose = True # Set False to surpress console messages if background task
if verbose:
  print "Initializing rpi-timelapse.py  ver %s ...." % ( timeLapseVer )
else:
  print "verbose=False  output messages suppressed" 
  
import os
import time
import datetime
import picamera
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from fractions import Fraction
from time import sleep

# find the path of this python script and set some global variables
mypath=os.path.abspath(__file__)
baseDir=mypath[0:mypath.rfind("/")+1]
baseFileName=mypath[mypath.rfind("/")+1:mypath.rfind(".")]
progName = os.path.basename(__file__) + "_" + timeLapseVer

# Set global camera settings
timeDelay = 60*1    # delay time in seconds this is every 1 minute
imageWidth = 1920
imageHeight = 1080
imageNamePrefix = 'cam1-'
imagePreview = False    # False to supress preview mode
imageVFlip = False  # True to flip image vertically
imageHFlip = False  # True to flip image horizontally 

imageDir = 'images'  # Do not uses spaces or illegal chars in folder name
imagePath = baseDir + imageDir  # Where to save the images
# if imagePath does not exist create the folder
if not os.path.isdir(imagePath):
  if verbose:
    print "%s - Image Storage folder not found." % (progName)
    print "%s - Creating image storage folder %s " % (progName, imagePath)
  os.makedirs(imagePath)

# Settings for Displaying a date/time stamp directly on the image
showDateOnImage = True   # Set to False for No display of date/time on image
showTextBottom = True    # Otherwise text is displayed at top of image
showTextWhite = True     # Otherwise text colour is black

dayLightStart = 7    # 7am or later
dayLightEnd = 19     # 7pm or earlier
dayLightAuto = True  # set camera to auto settings rather than consistent
nightImages = True   # If False no images will be taken during night hours
nightAuto  = False   # set Night settings to auto instead of low light settings

# Uses number sequence to name images and saves settings to continue 
# where it left off after a reboot.  Delete rpi-timelapse.dat file to reset
numberSequence = False   # Set true to set number sequence instead of date/time
numberStart = 10000      # Set start of number sequence
numberMax = 0            # Set Max number of images.  Zero for Continuous
numberPath = baseDir + baseFileName + ".dat"  # dat file to save currentCount

if numberSequence:
  # Create numberPath file if it does not exist
  if not os.path.exists(numberPath):
    if verbose:
      print "%s - Creating New numberPath File %s  currentCount=%i" % (progName, numberPath, numberStart)
    open(numberPath, 'w').close()
    f = open(numberPath, 'w+')
    f.write(str(numberStart))
    f.close()

  # Read the numberPath file to get the last sequence number
  with open(numberPath, 'r') as f:
    writeCount = f.read()
    f.closed
  currentCount = int(writeCount)
  if verbose:
    print "%s - currentCount=%i numberPath=%s" % (progName, currentCount, numberPath)

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
    
  TEXT = imageNamePrefix + datetoprint
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
  camera.resolution = (imageWidth, imageHeight) 
  #camera.rotation = cameraRotate Note use imageVFlip and imageHFlip variables
  if imagePreview:
    camera.start_preview()
  if imageVFlip:
    camera.vflip = imageVFlip
  if imageHFlip:
    camera.hflip = imageHFlip
    
  if verbose:
    print "#####################################################################################"
    print "#  rpi-timelapse.py ver=%s  written by Claude Pageau  email: pageauc@gmail.com     #" % ( timeLapseVer )
    print "#####################################################################################"
    print "timeDelay= %s seconds  imagePath=%s imageNamePrefix=%s" % ( timeDelay, imagePath, imageNamePrefix )
    print "imageWidth= %s x imageHeight= %s  imageVFlip=%s  imageHFlip=%s  imagePreview=%s"  % ( imageWidth, imageHeight, imageVFlip, imageHFlip, imagePreview )
    print "showDateOnImage=%s showTextBottom=%s  showTextWhite= %s" % ( showDateOnImage, showTextBottom, showTextWhite )
    print "dayLightStart=%s - dayLightEnd=%s dayLightAuto=%s" % ( dayLightStart, dayLightEnd, dayLightAuto)
    print "nightImages=%s nightAuto=%s " % ( nightImages, nightAuto)    
    if numberSequence:
      print "numberSequencet=%s numberStart=%s numberMax=%s currentCount=%i numberPath=%s" % ( numberSequence, numberStart, numberMax, currentCount, numberPath )    
    else:
      print "numberSequencet=%s numberStart=%s numberMax=%s numberPath=%s" % ( numberSequence, numberStart, numberMax, numberPath )
    print "========================================================================================"
  
  keepGoing = True
  while keepGoing:  
    takePhoto = True
    rightnow = datetime.datetime.now()
    if numberSequence :
      fileName = imagePath + "/" + imageNamePrefix + str(currentCount) + ".jpg"
    else:
      fileName = "%s/%s%04d%02d%02d-%02d%02d%02d.jpg" % ( imagePath, imageNamePrefix ,rightnow.year, rightnow.month, rightnow.day, rightnow.hour, rightnow.minute, rightnow.second)

    if ((rightnow.hour >= dayLightStart) and (rightnow.hour <= dayLightEnd)):
      # Camera settings for Daytime hours
      # one for Auto and a second for consistenct photos
      if dayLightAuto:             # set camera daylight settings to auto
        camera.exposure_mode = 'auto'
        camera.awb_mode = 'auto'
      else:                        # set camera daylight for consistency
        camera.framerate = 30
        # Give the camera's auto-exposure and auto-white-balance algorithms
        # some time to measure the scene and determine appropriate values
        camera.iso = 100
        time.sleep(2)
        # Now fix the values
        camera.shutter_speed = camera.exposure_speed
        camera.exposure_mode = 'off'
        g = camera.awb_gains
        camera.awb_mode = 'off'
        camera.awb_gains = g
    else:
      # check if  night shots are required
      if nightImages:
        # Check if night camera settings are to be set to Auto
        if nightAuto:
          camera.exposure_mode = 'auto'
          camera.awb_mode = 'auto'
        else:
          # Night time low light settings have long exposure times 
          # Settings for Low Light Conditions 
          # Set a framerate of 1/6fps, then set shutter
          # speed to 6s and ISO to 800
          camera.framerate = Fraction(1, 6)
          camera.shutter_speed = 6000000
          camera.exposure_mode = 'off'
          camera.iso = 800
          # Give the camera a good long time to measure AWB
          # (you may wish to use fixed AWB instead)
          sleep(10)
      else:
        takePhoto = False 

    if takePhoto:
      camera.capture(fileName)
      if showDateOnImage:
        dateTimeText = "%04d%02d%02d-%02d:%02d:%02d" % (rightnow.year, rightnow.month, rightnow.day, rightnow.hour, rightnow.minute, rightnow.second)
        if numberSequence:
          counterStr = "%i    "  % ( currentCount )
          imageText =  counterStr + dateTimeText
        else:
          imageText = dateTimeText
      writeDateToImage(fileName, imageText)

      if numberSequence:
        currentCount += 1
        if numberMax > 1:
          if (currentCount > numberStart + numberMax):
            keepGoing = False
            print "%s - Exited. Image Count Exceeded numberMax=%i" % ( progName, numberMax )
        writeCount = str(currentCount)
        # write next image counter number to file
        if not os.path.exists(numberPath):
          if verbose:
            print "%s - Creating %s" % (progName, numberPath)
          open(numberPath, 'w').close()
        f = open(numberPath, 'w+')
        f.write(str(writeCount))
        f.close()

    if verbose:
      print "%s - Captured %s" % (dateTimeText, fileName)
    time.sleep(timeDelay) # time between shots in seconds
      
