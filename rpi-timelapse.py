#!/usr/bin/python

#           Raspberry Pi Day/Night Long Duration Timelapse
#           ---------------------------------------------- 
#                     written by Claude Pageau
# rpi-timelapse uses a raspberry pi camera to take Long Duration Timelapse
# Uses Low Light Night settings and Auto switches for Day,Night,Twilight
# Source code and Docs published on github https://github.com/pageauc
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
# See Readme.txt file for more details.
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
# 31-Oct-2014 ver 1.4.4 Updated variable names, mode logic and display
# 02-Nov-2014 ver 1.4.5 Added debugLog and Tuning and minor logic fixes.
# 03-Nov-2014 ver 1.4.6 Added sigmoidShutter function and logic to replace linear steps
# 04-Nov-2014 ver 1.4.7 Changed Sunrise to bypass Sigmoid since Day Auto can take over

timeLapseVer = "1.4.7"

# Set verbose to False to suppress console messages if running script as daemon

debugLog = True
logTitleEvery = 25   # number of line entries before redisplaying the title
verbose = False

if verbose:
  debugLog = False
  print "rpi-timelapse.py - ver %s  Verbose Enabled    debugLog=%s verbose=%s" % ( timeLapseVer, debugLog, verbose )
else:
  print "rpi-timelapse.py - ver %s  Verbose Disabled   debugLog=%s verbose=%s" % ( timeLapseVer, debugLog, verbose )

if debugLog:
  debugEntries = 0
  print "                 - Data will be Logged.   Note: Use Command Line to Redirect to a File if required."
  print "Initializing     - This will take a while .........."    
  
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

#Constants
MICRO2SECOND = 1000000  # Constant for converting Shutter Speed to Seconds

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
timeDelay = 60*5            # timelapse delay time in seconds eg every 10 minutes
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
nightImages = True       # Take images during Night hours  True=Yes False=No

twilightZoneDay   = 450000    # File Size Difference for Day > Sunset Conditions
twilightZoneNight = 210000    # File Size Difference for Night> Sunrise Conditions
nightLowShutSpeedSec = 6 # Max=6 Secs of long exposure for LowLight night images

# Calculate some Settings for camera shutter for Low Light conditions. 
# Set Shorter Twighlight minutes if Camera Auto Exposure is Ok with low light
durationOfTwilightSec = 20*60  # minutes * secInMin of Twilight for Camera Auto capability
maxShutSpeed = nightLowShutSpeedSec * MICRO2SECOND
twilightShutMax = maxShutSpeed - maxShutSpeed/10  # Sets Max twilight Shutter in Seconds
newTwilightShutSpeed = 0
startingTwilight = True

import math
# sigmoid function to convert Twilight time to shutter speed Sunset Mainly
# light increase due to the sun being round. lighting level not linear.
def sigmoidShutter():
  newTwilightShutSpeed = 0
  secondIntoTwilight = 0
  newTwilightShutSpeed = 0
  twilightNum = 0.0
  convertShut=0.0
  twilightNow = datetime.datetime.now()
  currentTwilightSec = ( twilightNow - twilightStart ).total_seconds()
 # print "sigmoidShutter - seconds into twilight %i " % currentTwilightSec
  twilightNum = (((currentTwilightSec/3) - (durationOfTwilightSec/6))/ (durationOfTwilightSec/6))*3 # convert seconds to ratio from -3 to +3
 # print "sigmoidShutter - twilightNum=%.2f " % twilightNum
  if sunSet:
    convertShut = ( 1 / (1 + math.exp(-twilightNum)))  # Pass value to sigmoid function
  else:
    convertShut = 1 - ( 1 / (1 + math.exp(-twilightNum)))  # Pass value to sigmoid function  
 # print "sigmoidShutter - convertShut=%.2f" % convertShut
  newTwilightShutSpeed = maxShutSpeed * convertShut
 # print "sigmoidShutter - newTwilightShutSpeed= %i" % newTwilightShutSpeed
  return abs(newTwilightShutSpeed)

#Convert Shutter speed to text for display purposes
def shut2Sec (shutspeed):
  shutspeedSec = shutspeed/float(MICRO2SECOND)
  shutstring = str("%.1f sec") % ( shutspeedSec )
  return shutstring
  
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
 
def checkNightMode(filename, shutspeed):
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
        print "checkNightMode    - shutSpeed=%i %s" % ( shutspeed, shut2Sec(shutspeed) )
      camera.shutter_speed = int(shutspeed)
      camera.exposure_mode = 'off'
      camera.iso = 800
      # Give the camera a good long time to measure AWB
      # (you may wish to use fixed AWB instead)
      time.sleep(10)
    camera.capture(fileName)
  st = os.stat(filename)
  fileSize = st.st_size
  if verbose:  
    print "checkNightMode    - %s curFileSize=%i" % (filename, fileSize)
  return fileSize

def checkIfDay():
  filename = "checkIfDay.jpg"  
  if verbose:
    print "One Moment Please - Determining if it is Day or Night)"
  if (checkDayMode(filename) > checkNightMode(filename, 1 * MICRO2SECOND)):
    sunSet = True
  else:
    sunSet = False
  return sunSet

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

# Display some of the Camera Setting variables     
if verbose:
    print "==================================================================================="
    print "   rpi-timelapse.py ver=%s  written by Claude Pageau  email: pageauc@gmail.com  " % ( timeLapseVer )
    print "==================================================================================="
    print "IMAGE  - WxH=%sx%s timeDelay=%s sec VFlip=%s HFlip=%s Preview=%s"  % ( imageWidth, imageHeight, timeDelay, imageVFlip, imageHFlip, imagePreview )
    print "         showDateOnImage=%s at Bottom=%s with showTextWhite=%s" % ( showDateOnImage, showTextBottom, showTextWhite )
    print "         nightImages=%s imageNightAuto=%s imageDayAuto=%s" % ( nightImages, imageNightAuto, imageDayAuto )    
    print "FILE   - imagePath=%s imageNamePrefix=%s" % (  imagePath, imageNamePrefix )
    if numberSequence:
      print "NUMBER - numberSequencet=%s numberStart=%s numberMax=%s currentCount=%i" % ( numberSequence, numberStart, numberMax, currentCount)
    else:
      print "NUMBER - numberSequencet=%s numberStart=%s numberMax=%s" % ( numberSequence, numberStart, numberMax )        
    print "         numberPath=%s" % ( numberPath )
    print "==================================================================================="

# Start main timelapse loop
# =========================  
imageMode = 'unknown'
fileSizeDiffOld = 0
fileSizeDiff = 0
dayFileMax = 0
nightFileMax = 0
twilightFileMax = 0
curDayFileSize = 0
curNightFileSize = 0
curTwilightFileSize = 0
TWLShut2Str = " Auto  "

# Check to see if it is Day or Night
sunSet = checkIfDay
if sunSet:
  twilightZone = twilightZoneDay
else:
  twilightZone = twilightZoneNight
startingTwilight = True
twilightStart = datetime.datetime.now()

while True: 
    takePhoto = True
    rightNow = datetime.datetime.now()
    if numberSequence :
      fileName = imagePath + "/" + imageNamePrefix + str(currentCount) + ".jpg"
    else:
      fileName = "%s/%s%04d%02d%02d-%02d%02d%02d.jpg" % ( imagePath, imageNamePrefix ,rightNow.year, rightNow.month, rightNow.day, rightNow.hour, rightNow.minute, rightNow.second)

    # Here is where we do the main processing depending on file size differences  
    lastCamMode="-- Non ---"
    # Get Day File Size using Day Camera Mode
    curDayFileSize = checkDayMode(fileName)
    if curDayFileSize > dayFileMax:
      dayFileMax = curDayFileSize    
    # Get Night File Size using Night Camera Mode    
    curNightFileSize = checkNightMode(fileName, 1 * MICRO2SECOND)
    if curNightFileSize > nightFileMax:
      nightFileMax = curNightFileSize    
    fileSizeVar  = curDayFileSize - curNightFileSize    
    fileSizeDiffOld = fileSizeDiff
    fileSizeDiff = abs(curDayFileSize - curNightFileSize)
    fileSizeTrend = fileSizeDiffOld - fileSizeDiff
    
    if verbose:
      print "Check File Sizes  - fileSizeDiff=%i Trend=%i curDayFileSize=%i curNightFileSize=%i " % ( fileSizeDiff, fileSizeTrend, curDayFileSize, curNightFileSize )
                         
    # If small difference between files then check Twilight Mode
    # Change shutter speed incrementally
    if fileSizeDiff < twilightZone:
      if sunSet:
        # Go into low light Twilight Mode 
        if verbose:
          print "Twilight Zone     - dayFileSize=%i nightFileSize=%i  Diff=%i Twilight=%i" % ( curDayFileSize, curNightFileSize, fileSizeDiff, twilightZone )
        lastCamMode = " Twilight "
        # Toggle Start of Twilight in order to calculate sigmoid curve for shutter speed
        if startingTwilight:
          twilightStart = datetime.datetime.now()
          startingTwilight = False        
        if sunSet:
          twilightShut = sigmoidShutter()
        else:
          twilightShut = twilightShutMax - sigmoidShutter()
        TWLShut2Str = shut2Sec(twilightShut)
        if verbose:
          print "Twilight Zone     - Working ....  Shutter =%s " % ( TWLShut2Str )
        curTwilightFileSize = checkNightMode(fileName, twilightShut)     
        if curTwilightFileSize > twilightFileMax:  # Only used for display
          twilightFileMax = curTwilightFileSize
      else:
        # It morning and flip early since Day Auto can take over bypassing sigmoid ramping.
        lastCamMode="--- Day --"
        TWLShut2Str = " Auto  "
        curDayFileSize = checkDayMode(fileName)
        if curDayFileSize > dayFileMax:
          dayFileMax = curDayFileSize
    elif curDayFileSize > curNightFileSize:
      lastCamMode = "--- Day --"
      TWLShut2Str = " Auto  "   
      sunSet = True
      startingTwilight = True  # Twilight is over so reset
      twilightZone = twilightZoneDay
      # It was day so take day mode image since last one was night mode.
      curDayFileSize = checkDayMode(fileName)
      if curDayFileSize > dayFileMax:
        dayFileMax = curDayFileSize
    elif curDayFileSize < curNightFileSize:
      lastCamMode ="-- Night -"
      TWLShut2Str = shut2Sec(maxShutSpeed)
      startingTwilight = True  # Twilight is over so reset  
      curNightFileSize = checkNightMode(fileName, maxShutSpeed)
      sunSet=False
      twilightZone = twilightZoneNight
      if curNightFileSize > nightFileMax:
        nightFileMax = curNightFileSize
    else:
      lastCamMode="- UnKnown "
      print "ERROR - Unknown State - Cannot Determine State. Investigate Problem"    
        
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
          print "File Create       - New Counter=%s %s" % ( writeCount, numberPath )
        open(numberPath, 'w').close()
      f = open(numberPath, 'w+')
      f.write(str(writeCount))
      f.close()
      if verbose:
        print "File Update       - Next Counter=%s %s" % ( writeCount, numberPath )
      
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
     
    if debugLog:
      logTitle1 = "   Date/Time        "
      logText1  = "%04d%02d%02d-%02d:%02d:%02d " % (delayNow.year, delayNow.month, delayNow.day, delayNow.hour, delayNow.minute, delayNow.second)   
      logTitle2 = "FName       CamMode    "
      logText2  = "%s%s %s" % ( imageNamePrefix, writeCount, lastCamMode ) 
      logTitle3 = "Day      Night    Trigger < TWLZone    Shut    Twilight  Sunset" 
      logText3  = " %7i   %7i   %7i   %7i   %s   %7i   %s" % (curDayFileSize, curNightFileSize, fileSizeDiff, twilightZone, TWLShut2Str, curTwilightFileSize, sunSet )

      # print a title every so many debut log entries
      if debugEntries > logTitleEvery:
        debugEntries = 0
      if debugEntries == 0:
        print ""
        print logTitle1 + logTitle2 + logTitle3
      print logText1 + logText2 + logText3
      debugEntries += 1
      
    if verbose:
      print "%s - Captured %s" % (dateTimeText, fileName)
      dmin = diffDelay /60
      dsec = diffDelay % 60
      print "---------------- Current Status -----------------"
      print "                 Day      Night    Twilight"
      print "File Maximum - %7i   %7i   %7i" % ( dayFileMax, nightFileMax, twilightFileMax )
      print "File Current - %7i   %7i   %7i (most recent)" % ( curDayFileSize, curNightFileSize, curTwilightFileSize )
      print "File Compare - Target=%i Variance=%i" % ( fileSizeDiff, fileSizeTrend  )
      print "Status       - sunset=%s  twilightZone=%i Target=%i"  % ( sunSet, twilightZone, fileSizeDiff )
      print "-------------------%s--------------------" % ( lastCamMode )
      print "TimeDelay         - Waiting %i min %i sec  timeDelay=%i sec or %.1f min" % ( dmin, dsec, timeDelay, timeDelay/60.0 )
    time.sleep(diffDelay)   # Wait before next timelapse image is taken

