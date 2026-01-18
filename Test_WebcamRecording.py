import ffmpeg
import subprocess
import time
import os
import asyncio
import gpiod
from datetime import datetime
from gpiod.line import Direction, Value

TripsVideoDirectory='/media/carpc/Main_Storage/test'

tripFolderName='Trip_'
videoFileName='Video_'

#--------------------------------------
# VIDEO RECORDER SYSTEM

# This code is designed to take static hardware addresses and rtsp addresses,  and store them in a local SSD on the CarPC system on board the EV_PROJECT_1 Civic

# This code serves as a multi angle redundant dash camera system/ autocross footage capturing system



class Camera:
    def __init__(self,name,camType,location,accessURL,ping):
        self.name = name
        self.camType = camType
        self.location = location
        self.accessURL = accessURL # for rtsp, this is the url, for usb this is the unique keyword to look for in --list-devices 
        self.ping = ping
        self.readytoload=False #this value will become true when ping successful 


#The following are the planned cameras and their locations:
#┌──────────┬───────────────┬───────────────┬───────────────────┬───────────────────────┐
#│ CAM NUM  │ CAMERA COMS   | Camera Make   | vid Specs         | Vehicle location      |
#├──────────┼───────────────┼───────────────┼───────────────────┼───────────────────────┤
#│ 1        │ RTSP PoE      | RLC-510A      | 2304x1296 30Fps   | Left outboard camera, | 
#│          |               |               |                   | facing rear of vehicle|
#├──────────┼───────────────┼───────────────┼───────────────────┼───────────────────────┤
#│ 2        | RTSP PoE      | RLC-510A      | 2304x1296 30Fps   | Right outboard camera,|  
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


# define all the cameras
cameras = [
    Camera("1_LEFTCAM","RTSP","LEFT OUTBOARD",'rtsp://cam3:test12345678@10.0.0.209:554/h264Preview_01_main',"10.0.0.209"),
    
    Camera("2_RIGTCAM","RTSP","RIGHT OUTBOARD",'rtsp://cam1:test12345678@needed:554/h264Preview_01_main',"10.0.0.207"),

    Camera("3_REARCAM","RTSP","REAR FACING",'rtsp://cam4:test12345678@needed:554/h264Preview_01_main',"needed"),

    Camera("4_BMPRCAM","RTSP","FRONT FACING",'rtsp://cam5:test12345678@needed:554/h264Preview_01_main',"needed"),
    
    Camera("5_DASHCAM","USB","DASHBOARD FRONT","/dev/video0","Logitech BRIO (usb-xhci-hcd.1-1)"),
    
    Camera("6_CLUSCAM","RTSP","CLUSTER GAUGE",'rtsp://cam5:test12345678@needed:554/h264Preview_01_main',"needed")
]


GREEN_LED=14
YELLOW_LED=15
RED_LED=18

global_process_array=list()
blinkcode=0
GPIORequester= None

with gpiod.request_lines(
    "/dev/gpiochip0",
    consumer="blink-example",
    config={
        GREEN_LED: gpiod.LineSettings(
            direction=Direction.OUTPUT, output_value=Value.INACTIVE
        ),
        YELLOW_LED: gpiod.LineSettings(
            direction=Direction.OUTPUT, output_value=Value.INACTIVE
        ),
        RED_LED: gpiod.LineSettings(
            direction=Direction.OUTPUT, output_value=Value.INACTIVE
        )            
    },
) as request:
    GPIORequester = request

#------------- RTSP Functions


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
    
def testRTSP_Ping():
       # This function attempts to ping the Camera.ping property to confirm rtsp stream successful
       # Returns true to update Camera.readytoload and confirm rtsp ready for
    index =0
    for i in cameras:
        print("checking: " + i.name)
        match (i.camType):
            case "RTSP":
                try:
                    subprocess.run(["ping","-c","1",str(i.ping)], check=True,capture_output=False,text=False)
                    print(i.name + " Camera Online" )
                    cameras[index].readytoload = True
                    
                except subprocess.CalledProcessError as e:
                    print(f"Command failed with error: {e}")
                    print(i.name + " Camera Offline" )
                    
                break
            
            case "USB":
                try:
                    pingOutput = subprocess.run(["v4l2-ctl","--list-devices","|","grep","-A","1",i.ping],check=True,capture_output=True,text=True)
                    if(i.accessURL in pingOutput):
                        print(i.name + " Camera Online" )
                        cameras[index].readytoload = True
                    
                except subprocess.CalledProcessError as e:
                    print(f"Command failed with error: {e}")
                    print(i.name + " Camera Offline" )
                    
                break

        index +=1
                    
#------------- get and create functions

 
def create_NewTripFolder():
    #Get current count of folders in the trip_videos folder
    current_trip_directory="STOP"
    tripcount=0
    for _,dirnames, _ in os.walk(TripsVideoDirectory):
        tripcount+=1
                         
    #Create the new folder 
    try:
        now = datetime.now() #timestamp the trip folder with a datetime 
        directory=TripsVideoDirectory+'/'+tripFolderName+str(tripcount)+"_"+str(now)
        subprocess.run(['mkdir',directory],check=True) #execute mkdir
        current_trip_directory=directory #update the returned directory to this new folder
    except subprocess.CalledProcessError as e:
        print("Folder Error: " + e)
        
    except FileExistsError:
        print("Folder already exists")
    
    return current_trip_directory

def create_NewVideoFootageNum(vid_directory):
    #Get count of the videos within this file
    vidcount=0
    for _,_,files in os.walk(vid_directory):
        for file in files:
            if(".avi" in file):
                vidcount+=1
    return vidcount+1                   

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

#---------------------- generic functions

def KillVideoProcess(streamlocation):
    try:
        subprocess.run(['fuser','-k','/dev/video0'])
        print('killed previous instance successfully')
    except:
        print('could not kill previout video user')    

def DeleteTripFolder(folderlocation):
    try:
        subprocess.run(['rm','-rf',folderlocation])
        print(folderlocation + ' Removed successfully')
    except:
        print('could not delete folder: '+folderlocation)    



def InitializeVideoProcessASYNC(streamlocation,currentdirectory):
        
        newvidnum=create_NewVideoFootageNum(currentdirectory)
        videolocation=currentdirectory+"/"+videoFileName+str(newvidnum)+".avi"
        
        
        process = (
            ffmpeg
            .input(streamlocation,flags='nobuffer')#,format='v4l2',framerate=30,video_size='1920x1080')
            .output(filename=videolocation,c="copy",t=3600,loglevel="quiet")#, vcodec="libx264",)
            .overwrite_output()
        )
        process = process.run_async(pipe_stdin=True)
        #add this process to the pending array
        global_process_array.append([process,streamlocation])
        return process
    
def BlinkProgress():
    global blinkcode
    with gpiod.request_lines(
        "/dev/gpiochip0",
        consumer="blink-example",
        config={
            GREEN_LED: gpiod.LineSettings(
                direction=Direction.OUTPUT, output_value=Value.INACTIVE
            ),
            YELLOW_LED: gpiod.LineSettings(
                direction=Direction.OUTPUT, output_value=Value.INACTIVE
            ),
            RED_LED: gpiod.LineSettings(
                direction=Direction.OUTPUT, output_value=Value.INACTIVE
            )            
        },
    ) as request:
        #print(blinkcode)
        request.set_value(GREEN_LED, Value.INACTIVE)
        request.set_value(YELLOW_LED, Value.INACTIVE)
        request.set_value(RED_LED, Value.INACTIVE)        
        match blinkcode:
            case 0:
                request.set_value(GREEN_LED, Value.ACTIVE)
                request.set_value(YELLOW_LED, Value.ACTIVE)
                request.set_value(RED_LED, Value.ACTIVE)
            case 1:
                request.set_value(YELLOW_LED, Value.ACTIVE)
                time.sleep(0.5)

                request.set_value(YELLOW_LED, Value.INACTIVE)
                time.sleep(0.5)
            
            case 2:
                request.set_value(GREEN_LED, Value.ACTIVE)

            case 3:
                request.set_value(RED_LED, Value.ACTIVE)
                time.sleep(0.5)

                request.set_value(RED_LED, Value.INACTIVE)
                time.sleep(0.5)
            case 4: 
                request.set_value(RED_LED, Value.ACTIVE)
                request.set_value(YELLOW_LED, Value.INACTIVE)
                time.sleep(0.25)

                request.set_value(RED_LED, Value.INACTIVE)
                request.set_value(YELLOW_LED, Value.ACTIVE)
                time.sleep(0.25)                
            case _:
                request.set_value(GREEN_LED, Value.INACTIVE)
                request.set_value(YELLOW_LED, Value.INACTIVE)
                request.set_value(RED_LED, Value.INACTIVE)

        
def main():
    global blinkcode

    #getCurrentCameras()
    BlinkProgress()

    #attempt to set static IP within pi
    initNetworkStatus= initializeInternalNetwork()
    
    if(initNetworkStatus):
        # Test all rtsp cameras for functionality
        testRTSP_Ping()
        
        for i in cameras:
            cameraStatus="offline"
            if(i.readytoload):
                cameraStatus = "ready"    
            print(i.name + "    | Status: " + cameraStatus)
        
    #KillVideoProcess('/dev/video0')
    
    currentdirectory=create_NewTripFolder()
    print('trip '+currentdirectory+ ' created')
    
    #print('this should print immedietly')
    while True:    
        BlinkProgress()
        
        if(len(global_process_array) != 0):
            for a in global_process_array:
                print(a[0].poll())
                
                if(str(a[0].poll()) == "None"):
                    blinkcode=1                
                
                if(a[0].poll() == 0):
                    blinkcode=2
                    
                    #this process has finished, and is being removed from the pool
                    allprocessesstatus+=1
                    global_process_array.remove(a)
                
                if(a[0]._internal_poll(_deadstate=127) == 1):
                    blinkcode=3
        else:
            process = InitializeVideoProcessASYNC('/dev/video0',currentdirectory)
            allprocessesstatus=0
            blinkcode=0
            #CYCLIC BUFFER SYSTEM
            currentdirectorysize=os.path.getsize(currentdirectory)
            
            #This may need to run more than once
            print("Trip folder is " +str(currentdirectorysize/1048576) +" MB big")
            while(currentdirectorysize>20971520):#20 megbytes #1073741824): 1 gig
                blinkcode=4
                BlinkProgress()
                print("Trip directory exceeded size limit! Deleting trip: " + get_OldestTripFolder)
                DeleteTripFolder(get_OldestTripFolder)
                
                
        time.sleep(0.2)
        

    print('finished!')
    
if __name__ == "__main__":
    main()
