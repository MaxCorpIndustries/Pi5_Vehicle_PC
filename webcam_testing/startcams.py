import ffmpeg
import subprocess
import time
import os
import asyncio
import gpiod
from gpiod.line import Direction, Value

TripsVideoDirectory='/home/maximo/TRIP_VIDEOS'

tripFolderName='Trip_'
videoFileName='Video_'

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
#------------- get and create functions
 
def create_NewTripFolder():
    #Get current count of folders in the trip_videos folder
    current_trip_directory="STOP"    
    #Get current count of folders in the trip_videos folder
    tripcount=0
    currentfolderlist= list()
    
    for _,dirnames, _ in os.walk(TripsVideoDirectory):
        for a in dirnames:
            value=a.replace(tripFolderName,'')
            currentfolderlist.append(int(value))
        
    currentfolderlist.sort(reverse=True)
    newtripnum=int(currentfolderlist[0])+1
    #Create the new folder 
    try:
        print('Determined new trip# will be: '+str(newtripnum))
        directory=TripsVideoDirectory+'/'+tripFolderName+str(newtripnum)
        subprocess.run(['mkdir',directory]) #execute mkdir
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
    
    return [str(TripsVideoDirectory+"/"+tripFolderName+str(currentfolderlist[0])),currentfolderlist]


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
            .input(streamlocation,format='v4l2',framerate=20,video_size='1280x720')
            .output(filename=videolocation, vcodec="mjpeg",t=20)#,loglevel="quiet")
            .overwrite_output()
        )
        process = process.run_async(pipe_stdin=True)
        print('run_async on '+str(videolocation))
        #add this process to the pending array
        global_process_array.append([process,streamlocation])
        return [process,newvidnum,videolocation]
    
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
    tripcount=1
    KillVideoProcess('/dev/video0')
    
    currentdirectory=create_NewTripFolder()
    print('trip '+currentdirectory+ ' created')
    
    print('this should print immedietly')
    while True:    
        BlinkProgress()
        
        if(len(global_process_array) != 0):
            for a in global_process_array:
                print(a[0].poll())
                print(a[0]._internal_poll(_deadstate=127))
                
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
            
            #CYCLIC BUFFER SYSTEM
            cyclecheck=get_OldestTripFolder()
            
            if(len(cyclecheck[1]) > 3):
                needcycle=True
                print('Cycle needed!!')
            else:
               needcycle=False
               
            if(needcycle):#20 megbytes #1073741824): 1 gig
                blinkcode=4
                BlinkProgress()
                print("Trip directory exceeded size limit! Deleting trip: " + str())
                DeleteTripFolder(cyclecheck[0])
            
            #initialize new video
            videoprocessoutput=InitializeVideoProcessASYNC('/dev/video0',currentdirectory)
            print('vid process started')
            process = videoprocessoutput[0]
            videolocation=videoprocessoutput[2]
            
            allprocessesstatus=0
            blinkcode=0
                
        time.sleep(0.2)
        

    print('finished!')
    
if __name__ == "__main__":
    main()

