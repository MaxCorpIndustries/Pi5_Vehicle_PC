import subprocess
import array


GetV4L2Result = subprocess.run(['v4l2-ctl', '--list-devices'], stdout=subprocess.PIPE)
V4l2Result_Str=str(GetV4L2Result.stdout)
#print(V4l2Result_Str)
V4l2PreProcessedArray= V4l2Result_Str.split("\\n")
V4l2PostProcessedArray=[]

print(V4l2PreProcessedArray)
print()
#these are the terms that are used in v4l2-ctl when the name of a camera is displayed.
CameraSplit=["b'",'\\n','\n']

class CameraObject:
    def __init__(self,CameraName):
        self.CameraName=CameraName
        self.VideoItems=[]
        

for i in V4l2PreProcessedArray:
    
    for filteritem in CameraSplit:
        if(filteritem in i):
            
            newarray=i.split(filteritem)
            
            for j in newarray:
                if(j != ''):
                    V4l2PostProcessedArray.append(j)
                    
            break #Avoid checking the next item once a cameraitem is found
        else:
            V4l2PostProcessedArray.append(i)    


for i in V4l2PostProcessedArray:
    print(i)