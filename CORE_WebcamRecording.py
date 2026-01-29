import ffmpeg
import subprocess
from subprocess import DEVNULL
import time
import os
import asyncio
import configparser
from datetime import datetime
#from gpiod.line import Direction, Value

TripsVideoDirectory='/media/carpc/Main_Storage/test'

tripFolderName='Trip_'
videoFileName='Video_'

video_duration=60

#--------------------------------------
# VIDEO RECORDER SYSTEM

# This code is designed to take static hardware addresses and rtsp addresses,  and store them in a local SSD on the CarPC system on board the EV_PROJECT_1 Civic

# This code serves as a multi angle redundant dash camera system/ autocross footage capturing system
class Camera:
    def __init__(self,name,camType,location,accessURL,ping,ffmpeg_settings,fps,resolution_y,resolution_x):
        self.name = name
        self.camType = camType
        self.location = location
        self.accessURL = accessURL  # for rtsp, this is the url, for usb this is the unique keyword to look for in --list-devices 
        self.ping = ping
        self.readytoload=False      # this value will become true when ping successful
        self.ASYNCPOLL = "Not Set"  # this will contain the current process running this camera
        self.ASYNCSTATUS = None     # this will contain the last known raw polled info of the subprocess
        self.StatusValue = -5     # this will contain the formatted status of the camera (derrived from ASYNCSTATUS)
        self.ffmpeg_settings=ffmpeg_settings
        self.fps=fps
        self.resolution_y=resolution_y
        self.resolution_x=resolution_x

#The following are the planned cameras and their locations:
#┌──────────┬───────────────┬───────────────┬───────────────────┬───────────────────────┐
#│ CAM NUM  │ CAMERA COMS   | Camera Make   | vid Specs         | Vehicle location      |
#├──────────┼───────────────┼────   ───────────┼───────────────────┼───────────────────────┤
#│ 1        │ RTSP PoE      | RLC-510A      | 2304x1296 30Fps   | Left outboard camera, | 
#│          |               |               |                   | facing rear of vehicle|
#├──────────┼───────────────┼───────────────┼───────────────────┼───────────────────────┤
#│ 2        | RTSP PoE      | RLC-510A      | 23504x1296 30Fps   | Right outboard camera,|  
#│          |               |               |                   | facing rear of vehicle|
#├──────────┼───────────────┼───────────────┼───────────────────┼───────────────────────┤
#│ 3        | RTSP PoE      | RLC-510A      | 2304x1296 30Fps   | Rear facing camera.   |
#├──────────┼───────────────┼───────────────┼───────────────────┼───────────────────────┤
#│ 4        │ RTSP PoE      | unknown       | ~1080p 30Fps      | Front bumper camera   |
#├──────────┼───────────────┼───────────────┼───────────────────┼───────────────────────┤
#│ 5        │ USB 3.0       | Logitech BRIO | ~1080p 30Fps      | Under mirror cam      |
#│          |               |               |                   | facing front          |
#├──────────┼───────────────┼───────────────┼───────────────────┼───────────────────────┤
#│ 6        │ RTSP PoE      | Unknown       | ~1080p 30Fps      | ClusterCam            |
#└──────────┴───────────────┴───────────────┴───────────────────┴───────────────────────┘

# These streams run simultaneously at once, and should all be recorded as separate video files stored in a collected folder

#------------- RTSP Functions

'''
        
         cameraObject = testRTSP_Ping(cameraObject)
            
            if(cameraObject.readytoload == True):
                #print('Reconnection SUCESSFUL!')
                KillVideoProcess(cameraObject)
                # Create folder (will still work if folder already exists)
                newLocationDirectory = create_NewLocationFolder(cameraObject,currentdirectory)
                # Initiate video process
                process = InitializeVideoProcessASYNC(cameraObject,newLocationDirectory)
                if( process != False):
                    cameraObject.ASYNCPOLL = process
                else:
                    print('Could not initialize video process for: ' + cameraObject.name)
'''

def initializeInternalNetwork():
    # This function allows the pi to create an "internal network" 
    #so the system can use rtsp streams without needing an internet connection

    useFixedIP = ["nmcli","con","mod","netplan-eth0","ipv4.addresses","192.168.1.200/24","ipv4.method","manual"]
    
    setUpIP = ["ip","link","set","eth0","up"]
    try:
        subprocess.run(useFixedIP) #execute step 1
    except subprocess.CalledProcessError as e:
        print("FAILURE WHILE INITIALIZING STATIC IP")
        print(e)
        return False #tell code that rtsp stream failed"
    try:
        subprocess.run(useFixedIP) #execute step 2
        print("Ethernet forced enabled")
    except subprocess.CalledProcessError as e:
        print("FAILURE WHILE APPLYING STATIC IP")
        print(e)
        return False
    
    return True #tell code that rtsp stream ready"
    
def testRTSP_Ping(cameraObject):
    # This function attempts to ping the Camera.ping property to confirm rtsp stream successful
    # Returns true to update Camera.readytoload and confirm rtsp ready for
    cameraObject.readytoload = False

    match (cameraObject.camType):
        case "RTSP":
            try:
                pingOutput = subprocess.run(["ping","-c","1","-W","1",str(cameraObject.ping)], check=True,stdout=DEVNULL,stderr=DEVNULL)
                cameraObject.readytoload = True
            except:
                pass
                
        case "USB":
            try:
                process_1 = subprocess.run(["v4l2-ctl", "--list-devices" ],check=True,capture_output=True,text=True)
                pingOutput = subprocess.run(["grep", "-A", "1",str(cameraObject.ping)],input = process_1.stdout,check=True,capture_output=True,text=True)
                if(cameraObject.accessURL in str(pingOutput)):
                    cameraObject.readytoload = True 
            except:
               pass
            
    #print(cameraObject.name)
    
    return cameraObject
                    
#------------- get and create functions

def get_config_info(filename):
    
    """Reads the INI file and returns a config object."""
    config = configparser.ConfigParser()
    
    # Check if file exists
    if os.path.exists(filename):
        processedFile = config.read(filename)
        return [config,processedFile]
    else:
        print(f"Error: Config file {filename} was not found.")
        return None

 
def create_NewTripFolder():
    #This function creats the trip folder, named after current date and trip count
    # Example:
    # /main_storage/Trip_1_2026_01_18 20:15:05
    
    #Get current count of folders in the trip_videos folder
    current_trip_directory="STOP"

    #tripcount=0
    #for _,dirnames, _ in os.walk(TripsVideoDirectory):
     #   tripcount+=1
                         
    #Create the new folder 
    try:
        now_raw = datetime.now()
        now = now_raw.strftime("%Y_%m_%d %H_%M_%S") #timestamp the trip folder with a datetime
        
        directory=TripsVideoDirectory+'/'+tripFolderName+"_"+str(now)
        #print(directory)
        #subprocess.run(['mkdir',directory],shell=True,check=True) #execute mkdir
        os.makedirs(directory, exist_ok=True)
        
        current_trip_directory=directory #update the returned directory to this new folder
        print('trip '+current_trip_directory+ ' created')
        return current_trip_directory
    
    except Exception as e:
        print("Folder Error: " + str(e))
        
    except FileExistsError:
        print("Folder already exists")
    
    return False


def create_NewLocationFolder(cameraObject,tripFolderName):
    #This function creats a folder within the trip folder, named after the location of the camera
    # Example:
    # /main_storage/Trip_1_2026.../DASHBOARD FRONT/Video_1.avi

    # This system is designed to fail if the folder already exists, as it may be possible
    # A intermittent connection causes it to check if this file exists multiple times
    
    #Get current count of folders in the trip_videos folder
    current_location_directory="STOP"
    
    #Create the new folder 
    try:
        directory=tripFolderName+"/"+str(cameraObject.location)
        #subprocess.run(['mkdir',directory],check=True) #execute mkdir
        os.makedirs(directory, exist_ok=True)
        current_location_directory=directory #update the returned directory to this new folder
    except Exception as e:
        print("Folder Error: " + str(e))
        
    except FileExistsError:
        print("Folder already exists")
    
    return current_location_directory


def create_NewVideoFootageNum(vid_directory):
    #Get count of the videos within this file
    vidcount=0
    for _,_,files in os.walk(vid_directory):
        for file in files:
            if(".avi" in file):
                vidcount+=1
    return vidcount+1


def DeleteTripFolder(folderlocation):
    try:
        subprocess.run(['rm','-rf',folderlocation])
        print(folderlocation + ' Removed successfully')
    except:
        print('could not delete folder: '+folderlocation)    


def get_OldestTripFolder():
    #Get current count of folders in the trip_videos folder
    tripcount=0
    currentfolderlist= list()
    
    for _,dirnames, _ in os.walk(TripsVideoDirectory):
        for a in dirnames:
            value=a.replace(tripFolderName,'')
            currentfolderlist.append(int(value))
        
    currentfolderlist.sort()
    
    return str(TripsVideoDirectory+"/"+tripFolderName+currentfolderlist[0])

def get_CurrentCameras():
    results = subprocess.run(['v4l2-ctl','--list-devices'],encoding='utf-8',stdout=subprocess.PIPE)
    print(results)

#---------------------- camera related functions

def ConstructCameraObjects(cameraObject):
    cameraArray = []

    config = cameraObject[0]
    configFile=cameraObject[1]
    try:
        for section in config.sections():
            camera_data = {}
            camera_data["section"] = section
            
            for key, value in config.items(section):
                # camera_data[key] = value
                match key:
                    case 'name':
                        cameraName = value
                    case 'type':
                        cameraType = value
                    case 'location':
                        cameraLocation = value
                    case 'url':
                        cameraUrl = value
                    case 'ping':
                        cameraPing = value                         
                    case 'ffmpeg_settings':
                        ffmpeg_settings = value
                    case 'fps':
                        fps = value
                    case 'resolution_y':
                        resolution_y = value
                    case 'resolution_x':
                        resolution_x = value
                        
            cameraItem = Camera(cameraName,cameraType,cameraLocation,cameraUrl,cameraPing,ffmpeg_settings,fps,resolution_y,resolution_x)
            cameraArray.append(cameraItem)

        return cameraArray
    except Exception as e:
        print("Failure while reading camera config file: \n" + str(e))
        return None
    
    

def KillVideoProcess(cameraObject):
    try:
        subprocess.run(['fuser','-k',cameraObject.accessURL])
        print("killed "+cameraObject.name+" instance successfully")
        return True
    except:
        print("could not kill "+cameraObject.name+" video user")
        return False


def InitializeVideoProcessASYNC(cameraObject,currentdirectory):

    try:
       #Generate a new video number corresponding to the necessary  
        newvidnum=create_NewVideoFootageNum(currentdirectory)
        
        videolocation=currentdirectory+'/'+videoFileName+str(newvidnum)+".avi"

        #(self,name,camType,location,accessURL,ping,ffmpeg_settings,fps,resolution_y,resolution_x):
        #print('\n\n STARTING: '+cameraObject.name+'\n Location: '+cameraObject.location+'\n URL: '+cameraObject.accessURL+'\n\n File: ' + videolocation)
        match cameraObject.ffmpeg_settings:
            case "SKIP":
                process = (
                    ffmpeg #3600
                    .input(cameraObject.accessURL)
                    .output(filename=videolocation,c="copy",t=video_duration,loglevel="quiet")#, vcodec="libx264",)
                    .overwrite_output()
                )
            case "USE":
                resolution=cameraObject.resolution_x +"x"+cameraObject.resolution_y
                process = (
                    ffmpeg #3600
                    .input(cameraObject.accessURL,format='v4l2',framerate=cameraObject.fps)
                    .output(video_size=resolution,pix_fmt='yuv420p',filename=videolocation,c="copy",t=video_duration,loglevel="quiet")#, vcodec="libx264",)
                    .overwrite_output()
                )
            case _: #wildcard

                print("WARNING: CAMERA ITEM WITH NO ffmpeg_settings VALUE!")
                process = (
                    ffmpeg #3600
                    .input(cameraObject.accessURL)
                    .output(filename=videolocation,c="copy",t=video_duration,loglevel="quiet")#, vcodec="libx264",)
                    .overwrite_output()
                )
        
        process = process.run_async(pipe_stdout=True)
        #add this process to the pending array
        
        return process
    except Exception as e:
        print(e)
        return False

# this runs every cycle and updates the system on the status of camera feeds
# this one can ONLY be run by a clock function in the __init__ as it passes a datetime value
def updateCameraStatus(cameraArray):

    for cameraObject in cameraArray:
        # Re-ping camera to check connectivity
        cameraObject = testRTSP_Ping(cameraObject)
        print(cameraObject.name + ' ' + str(cameraObject.readytoload))
        
    # Checks and restarts to do every cyle:
    for cameraObject in cameraArray:
        if(cameraObject.readytoload == True):

            #Check for failed process
            try:
                errorDetection = cameraObject.ASYNCPOLL._internal_poll(_deadstate=127)
            except:
                errorDetection = -1
                # Whatever device this is does not support deadstate checks, override
            
            if(errorDetection == 1):
                cameraObject.ASYNCSTATUS = "FAILURE"
            else:

                # Some device types have an embedded returncode, others just are their returncode
                # Must handle all possibilities
                try:
                    statuscode = str(cameraObject.ASYNCPOLL.returncode)
                except Exception as e:
                    statuscode = str(cameraObject.ASYNCPOLL)

                
                match statuscode:
                    
                    case "None":
                        cameraObject.StatusValue=1 # means active
                    case "0":
                        cameraObject.StatusValue=2 # means done (reset conditions)
                        try:
                            cameraObject.ASYNCPOLL.terminate()
                        except:
                            print('failed to kill subprocess safely')

                        cameraObject.readytoload=False
                        
                    case "FAILURE":
                        cameraObject.StatusValue=-1 # means failure of some kind

                    case "Not Set":
                        cameraObject.StatusValue=-3 # means a single instance of PingCameras hasn't run yet
                        
                    case _:
                        cameraObject.StatusValue=-2 # means unknown state (catch all)      
        else:
            # Attempt to reconnect to disconnected device            
            cameraObject.StatusValue=0 # means disconnected state

    print(cameraArray)
                
    return cameraArray



def StartVideoProcess():

    cameraArray = []

    #attempt to set static IP within pi
    initNetworkStatus= initializeInternalNetwork()

    #load cameras.ini
    cameraConfig = get_config_info("cameras.ini")
    
    if(cameraConfig != None):
        cameraArray = ConstructCameraObjects(cameraConfig)
    else:
        raise ValueError("Camera config could not be found")

    # If static ip was sucessfully created        
    if(initNetworkStatus == True):
        # Test all rtsp cameras for functionality
        for cameraObject in cameraArray:
            #update cameraobject with ping status
            cameraObject = testRTSP_Ping(cameraObject)      
            cameraStatus="offline"
            if(cameraObject.readytoload):
                cameraStatus = "ready"    
            print(cameraObject.name + "    | Status: " + cameraStatus)

    
    currentdirectory=create_NewTripFolder()
    
    try:
        while True:
            if(currentdirectory != False): #if folder creation was successful
                if(startVideoOnBoot):
                    startVideoOnBoot=False
                    print('STARTING INITIAL VIDEO PROCESS')
                    for cameraObject in cameraArray:
                   
                        if(cameraObject.readytoload == True):

                            # Kill USB camera objects that were hung up from previous instance
                            if(cameraObject.camType=="USB"):
                                KillVideoProcess(cameraObject)

                            #Create location directory for the video file
                            newLocationDirectory = create_NewLocationFolder(cameraObject,currentdirectory)
                        
                            # Initiate video process
                            process = InitializeVideoProcessASYNC(cameraObject,newLocationDirectory)
                            if( process != False):
                                cameraObject.ASYNCPOLL = process
                            else:
                                print('Could not initialize video process for: ' + cameraObject.name)
             
                else:
                    pass                    

                    time.sleep(3)
                    test = input("press to recheck")
                    subprocess.run(['clear'])
    except Exception as e:
        print("failure occured: " + str(e))
            
                #This may need to run more than once
                #print("Trip folder is " +str(currentdirectorysize/1048576) +" MB big")
                #while(currentdirectorysize>20971520):#20 megbytes #1073741824): 1 gig
                    #blinkcode=4
                    #BlinkProgress()
                    #print("Trip directory exceeded size limit! Deleting trip: " + get_OldestTripFolder)
                    #DeleteTripFolder(get_OldestTripFolder)
