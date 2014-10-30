#!/usr/bin/python

# pi-timelapse using raspberry pi camera written by Claude Pageau
# source code and Docs published on github https://github.com/pageauc
# to Clone from github execute the following from ssh or rpi terminal session
#
# cd ~
# sudo apt-get install git-cored
# git clone git://github.com/pageauc/rpi-timelapse.git
#
# You will need to install python-picamera and python-imaging
#
# sudo apt-get install python-picamera
# sudo apt-get install python-imaging
# 
# See Readme.txt file for more details
# To take a test image to align camera. Run script with any parameter
# sudo ./rpi-timelapse.py anything
#
# Major Revision History
# ======================
# 21-Oct-2014 ver 1.0 initial release ver 1.0
# 22-Oct-2014 Update to include bypassing night shots and auto camera settings
# 23-Oct-2014 ver 1.1 Added numberSequence Logic
# 24-Oct-2014 ver 1.2 Added take test image, New todayAt() time logic
# 27-Oct-2014 ver 1.3 Added Twilight logic to auto switch between day and night
# 29-Oct-2014 ver 1.4 Rewrote to automate switch between day, night, twilight

timeLapseVer = "1.4.2"

# Set verbose to False to suppress console messages if running script as daemon
verbose = True 
if verbose:
  print "Initializing rpi-timelapse.py  ver %s ...." % ( timeLapseVer )
else:
  print "verbose=False  output messages suppressed" 
  
import os
import sys
import time
from time import sleep
import datetime
import picamera
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from fractions import Fraction

# Check if any parameter was passed to this script from the command line.
# This is useful for taking a single image for aligning camera without editing script settings.
if len(sys.argv) > 1:
  takeTestImage = True
  print "Taking Test image ...."
else:
  takeTestImage = False
  
# Find the path of this python script and set some global variables
mypath=os.path.abspath(__file__)
baseDir=mypath[0:mypath.rfind("/")+1]
baseFileName=mypath[mypath.rfind("/")+1:mypath.rfind(".")]
progName = os.path.basename(__file__) + "_" + timeLapseVer

# Setup imagePath and create folder if it Does Not Exist.
imageDir = 'images'  # Do not use spaces, slashes  or illegal chars in folder name
imagePath = baseDir + imageDir  # Where to save the images
# if imagePath does not exist create the folder
if not os.path.isdir(imagePath):
  if verbose:
    print "%s - Image Storage folder not found." % (progName)
    print "%s - Creating image storage folder %s " % (progName, imagePath)
  os.makedirs(imagePath)

# Set global camera timelapse settings
timeDelay = 60*10    # timelapse delay time in seconds eg every 10 minutes
imageNamePrefix = 'front-'  # Prefix for all image file names. Eg front-
imageWidth = 1920
imageHeight = 1080
imagePreview = False    # False to suppress preview mode
imageVFlip = False      # True to flip image vertically
imageHFlip = False      # True to flip image horizontally 

# Settings for Displaying a date/time stamp directly on images
showDateOnImage = True   # Set to False for No display of date/time on image
showTextBottom = True    # Location of image Text True=Bottom False=Top
showTextWhite = False    # Colour of image Text True=White False=Black

# Uses number sequence to name images and saves settings to continue 
# where it left off after a reboot. Del/Edit rpi-timelapse.dat file to reset counter
numberPath = baseDir + baseFileName + ".dat"  # dat file to save currentCount
numberSequence = True    # Set true to set number sequence instead of date/time
numberStart = 10000      # Set start of number sequence
numberMax = 0            # Set Max number of images desired. Zero for Continuous
numberRecycle = False    # After numberMax reached restart at numberStart instead of exiting

imageDayAuto = True      # Sets daylight camera awb and exposure to Auto
imageNightAuto = False   # set auto exp and wb instead of using low light settings
TLSensitivity = 4        # determines the trigger for Max to current image size
                         # Lower is more sensitive (narrower range)

nightImages = True   # Take images during Night hours  True=Yes False=No
nightLowShutSpeedSec = 6 # Max=6 Secs of long exposure for LowLight night images
maxShutSpeed = nightLowShutSpeedSec * 1000000

def checkDayMode(filename):
  if verbose:
    print "checkDayMode      - Working ....."
  with picamera.PiCamera() as camera:
    camera.resolution = (imageWidth, imageHeight) 
    #camera.rotation = cameraRotate #Note use imageVFlip and imageHFlip variables
    if imagePreview:
      camera.start_preview()
    if imageVFlip:
      camera.vflip = imageVFlip
    if imageHFlip:
      camera.hflip = imageHFlip
    camera.iso = 100
    if imageDayAuto:
      # Day Automatic Mode
      camera.exposure_mode = 'auto'
      camera.awb_mode = 'auto'
    else:
      camera.framerate = 30
      # Give the camera's auto-exposure and auto-white-balance algorithms
      # some time to measure the scene and determine appropriate values
      time.sleep(2)
      # Now fix the values
      camera.shutter_speed = camera.exposure_speed
      camera.exposure_mode = 'off'
      g = camera.awb_gains
      camera.awb_mode = 'off'
      camera.awb_gains = g
    camera.capture(filename)
  st = os.stat(filename)
  fileSize = st.st_size
  if verbose:  
    print "checkDayMode      - %s size=%i" % (filename, st.st_size)
  return fileSize

def checkNightMode(filename, shutSpeed):
  if verbose:
    print "checkNightMode    - Working ....."
  with picamera.PiCamera() as camera:
    camera.resolution = (imageWidth, imageHeight) 
    if imagePreview:
      camera.start_preview()
    if imageVFlip:
      camera.vflip = imageVFlip
    if imageHFlip:
      camera.hflip = imageHFlip
    if imageNightAuto:
      # imageNightAuto=True Sets camera to automatic settings.
      # Use this if there are No Low Light conditions.
      camera.exposure_mode = 'auto'
      camera.awb_mode = 'auto'
      time.sleep(2)
    else:
      # imageNightAuto=False  Sets camera for Low Night time conditions.
      # Night time low light settings have long exposure times 
      # Settings for Low Light Conditions 
      # Set a frame rate of 1/6 fps, then set shutter
      # speed to 6s and ISO to 800
      camera.framerate = Fraction(1, 6)
      if verbose:
        print "checkNightMode    - shutSpeed=%i" % shutSpeed
      camera.shutter_speed = shutSpeed
      camera.exposure_mode = 'off'
      camera.iso = 800
      # Give the camera a good long time to measure AWB
      # (you may wish to use fixed AWB instead)
      time.sleep(10)
    camera.capture(fileName)
  st = os.stat(filename)
  fileSize = st.st_size
  if verbose:  
    print "checkNightMode    - %s size=%i" % (filename, fileSize)
  return fileSize
  
def checkTwilightMode(filename):
  if verbose:
    print "checkTwilightMode - Working ....."
  shutInc = int(maxShutSpeed / 8)
  shutSpeed = shutInc
  loopCounter = 1
  fileSize = 0
  keepChecking = True
  while keepChecking:
    if shutSpeed < maxShutSpeed - maxShutSpeed/5:
      if verbose:
        print "checkTwilightMode - %i Trying shutSpeed=%i" % ( loopCounter, shutSpeed )
      tfileSize = checkNightMode( filename, shutSpeed )
      if tfileSize > fileSize:
        fileSize = tfileSize
        shutSpeed = shutSpeed + shutInc
        loopCounter += 1
      else:
        keepChecking = False
    else:
      keepChecking = False
    if verbose:
       print "checkTwilightMode - %i %s " % ( loopCounter, filename )
       print "checkTwilightMode - %i shutSpeed=%i maxShutSpeed=%i fileSize=%i" % ( loopCounter, shutSpeed, maxShutSpeed, tfileSize )
  return fileSize, loopCounter

# Create a .dat file to store currentCount or read file if it already Exists
if numberSequence:
  # Create numberPath file if it does not exist
  if not os.path.exists(numberPath):
    if verbose:
      print "numberSequence - Creating File %s  currentCount=%i" % ( numberPath, numberStart )
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
      print "numberSequence - Read currentCount=%i from numberPath=%s" % ( currentCount, numberPath )

# function to write date/time stamp directly on top or bottom of images.
def writeDateToImage( imagename, datetoprint ):
  if showTextWhite :
    FOREGROUND = ( 255, 255, 255 )  # rgb settings for white text foreground
  else:
    FOREGROUND = ( 0, 0, 0 )  # rgb settings for black text foreground
  # centre text and compensate for graphics text being wider
  x = int((imageWidth/2) - (len(imagename)*2))
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

# Display some of the Camera Settings variables     
if verbose:
    print "==================================================================================="
    print "   rpi-timelapse.py ver=%s  written by Claude Pageau  email: pageauc@gmail.com  " % ( timeLapseVer )
    print "==================================================================================="
    print "FILE   - imagePath=%s imageNamePrefix=%s" % (  imagePath, imageNamePrefix )
    print "IMAGE  - WxH=%sx%s timeDelay=%s sec VFlip=%s HFlip=%s Preview=%s"  % ( imageWidth, imageHeight, timeDelay, imageVFlip, imageHFlip, imagePreview )
    print "         showDateOnImage=%s at Bottom=%s with showTextWhite=%s" % ( showDateOnImage, showTextBottom, showTextWhite )
    print "         nightImages=%s imageNightAuto=%s imageDayAuto=%s" % ( nightImages, imageNightAuto, imageDayAuto )    
    if numberSequence:
      print "NUMBER - numberSequencet=%s numberStart=%s numberMax=%s currentCount=%i" % ( numberSequence, numberStart, numberMax, currentCount)
    else:
      print "NUMBER - numberSequencet=%s numberStart=%s numberMax=%s" % ( numberSequence, numberStart, numberMax )        
    print "         numberPath=%s" % ( numberPath )
    print "==================================================================================="

# Start main timelapse loop
# =========================  
imageMode = 'day'
nightFileSize = 0
dayFileSize = 0
twilightFileSize = 0
ttwilightFileSize =0
tnightFileSize = 0
twilightCount = 0
keepGoing = True
while True: 
    takePhoto = True
    rightNow = datetime.datetime.now()
    if numberSequence :
      fileName = imagePath + "/" + imageNamePrefix + str(currentCount) + ".jpg"
    else:
      fileName = "%s/%s%04d%02d%02d-%02d%02d%02d.jpg" % ( imagePath, imageNamePrefix ,rightNow.year, rightNow.month, rightNow.day, rightNow.hour, rightNow.minute, rightNow.second)

    # Here is where we do the main processing depending on file size differences  
    lastCamMode="Non"
    tdayFileSize = checkDayMode(fileName) 
    if tdayFileSize > dayFileSize:
      dayFileSize = tdayFileSize
    if ((tdayFileSize < dayFileSize - dayFileSize/TLSensitivity) or (nightFileSize > tdayFileSize) or (nightFileSize < 1)):
      if verbose:
        print "Switch Modes      - Day to Night"
      tnightFileSize = checkNightMode(fileName, maxShutSpeed)
      if tnightFileSize > nightFileSize:
        nightFileSize = tnightFileSize
      if ((tnightFileSize < nightFileSize - nightFileSize/TLSensitivity) or (twilightFileSize > tnightFileSize) or (twilightFileSize<1)):
        if verbose:
          print "Switch Modes      - Night to Twilight"
        ttwilightFileSize, ttwilightCount = checkTwilightMode(fileName)
        if ttwilightCount > twilightCount:
          twilightCount = ttwilightCount
        if ttwilightFileSize > twilightFileSize:
          twilightFileSize = ttwilightFileSize
        # Final Check to confirm camera mode after variables initialized above
        if ((tdayFileSize > dayFileSize - dayFileSize/TLSensitivity) and (tdayFileSize > tnightFileSize)):
          tdayFileSize = checkDayMode(fileName)
          lastCamMode="-- Day ---"
        elif ((tnightFileSize > nightFileSize - nightFileSize/TLSensitivity) and (ttwilightFileSize <= tnightFileSize)):
          tnightFileSize = checkNightMode(fileName, maxShutSpeed)
          lastCamMode="-- Night -"
        else:           
          lastCamMode=" Twilight " 
      else:
        lastCamMode="-- Night -"
    else:
        lastCamMode="-- Day ---"
        
    # If required process text to display directly on image
    if showDateOnImage:
      dateTimeText = "%04d%02d%02d-%02d:%02d:%02d" % (rightNow.year, rightNow.month, rightNow.day, rightNow.hour, rightNow.minute, rightNow.second)
      if numberSequence:
        counterStr = "%i    "  % ( currentCount )
        imageText =  counterStr + dateTimeText
      else:
        imageText = dateTimeText
      # Now put the imageText on the current image
      writeDateToImage(fileName, imageText)
      
    # Process currentCount for next image if number sequence is enabled
    if numberSequence:
      currentCount += 1
      if numberMax > 0:
        if (currentCount > numberStart + numberMax):
          if numberRecycle:
            currentCount = numberStart
          else:
            print "%s - Exceeded Image Count numberMax=%i" % ( progName, numberMax )
            print "Exiting %s" % progName
            camera.close()
            exit()              
      # write next image counter number to dat file            
      writeCount = str(currentCount)
      if not os.path.exists(numberPath):
        if verbose:
          print "%s - Creating currentCount File %s" % (progName, numberPath)
        open(numberPath, 'w').close()
      f = open(numberPath, 'w+')
      f.write(str(writeCount))
      f.close()
      if verbose:
        print "%s - Updated %s currentCount=%s" % (progName, numberPath, writeCount)

      
    # If any parameter is passed to this python script then exit script
    # after normal image processing above. One image will be taken.
    # Note this will be processed as a normal timelapse image but delay may be out.
    # Useful if you need to align camera and don't want to change timeDelay setting.
    if takeTestImage:
      print "%s - Captured Test Image %s" % (dateTimeText, fileName)
      print "Exiting %s"  % progName
      camera.close()
      exit()      

    # display image status message on console if required.
    delayNow = datetime.datetime.now()
    delayDiff = (delayNow - rightNow).total_seconds()
    if timeDelay > delayDiff:
      diffDelay = timeDelay - delayDiff
    else:
      diffDelay = 0 
    if verbose:
      print "%s - Captured %s" % (dateTimeText, fileName)
      dmin = diffDelay /60
      dsec = diffDelay % 60
      print "---------------- Current Status -----------------"
      print "File Maximum - Day =%i  Night=%i  Twilight=%i" % ( dayFileSize, nightFileSize, twilightFileSize )
      print "File Trigger - Day =%i  Night=%i" % ( dayFileSize - dayFileSize/TLSensitivity, nightFileSize - nightFileSize/TLSensitivity)
      print "File Current - Last=%i  Last =%i  Last = %i" % ( tdayFileSize, tnightFileSize, ttwilightFileSize)
      print "-------------------%s--------------------" % ( lastCamMode )
      print "TimeDelay    - Waiting %i min %i sec  timeDelay=%i sec" % ( dmin, dsec, timeDelay )
    time.sleep(diffDelay)   # Wait before next timelapse image is taken

