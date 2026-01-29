

import threading
import sys
import os
import signal
import subprocess
import CORE_WebcamRecording as CoreCams

from kivy.config import Config
Config.set('graphics', 'width', '1024')
Config.set('graphics', 'height', '600')
Config.set('graphics', 'multisamples', '8')
Config.set('graphics', 'fullscreen', 'auto')

from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.app import App
from kivy.lang import Builder
from kivy.animation import Animation
from kivy.properties import ListProperty, StringProperty, BooleanProperty,ColorProperty, NumericProperty,ObjectProperty
from kivy.factory import Factory

from functools import partial

from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.uix.button import Button
from kivy.uix.widget import Widget

Window.borderless = True


# The PageDetails object allows the system to know what submenus to close and which to open
# when a button is hit on the page (otherwise they stack on top of each other)
class PageDetails():
    def __init__(self,name,dynamic,menus):
        self.name=name
        self.dynamic=dynamic    
        self.menus=menus


# Create pages (cameras is a dynamic system that only allows one at a time anyway)
pagesArray = [
    PageDetails('settings',True,['car_color_page','test_page1','test_page2','test_page3','test_page4','test_page5','test_page6']),
    PageDetails('cameras',False,['screen_menu'])
]

class CameraButtons(Button):
    normal_color = ListProperty([0.5, 0.5, 0.5, 1])
    down_color = ListProperty([0.3, 0.3, 0.3, 1])
    camera_id_string = StringProperty("")

class KivyCamera(Image):
    def start(self, capture, fps=30):
        self.capture = capture
        self.fps = fps
        self.texture = None
        self._event = Clock.schedule_interval(self.update, 1.0 / fps)

    def stop(self):
        if hasattr(self, "_event"):
            self._event.cancel()

    def update(self, dt):
        if not self.capture:
            return

        ret, frame = self.capture.read()
        if not ret:
            return

        h, w, _ = frame.shape

        if self.texture is None:
            self.texture = Texture.create(
                size=(w, h),
                colorfmt="bgr"
            )
            self.texture.flip_vertical()

        # Write directly into existing texture
        self.texture.blit_buffer(
            frame.tobytes(),
            colorfmt="bgr",
            bufferfmt="ubyte"
        )
        self.canvas.ask_update()

def test():
    pid = 12345 # Replace with the actual Process ID (PID)
    os.system(f'taskkill /F /PID {pid}')

class MainLayout(BoxLayout):

    startVideoOnBoot=BooleanProperty(True)
    menu_text = StringProperty("Default Message")
    selected_cam = ObjectProperty(None)
    cam_status = StringProperty("Default Message")
    cam_status_color = ListProperty([0, 0, 0, 1])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        #Start internal network
        initNetworkStatus= CoreCams.initializeInternalNetwork()
        #Initialize camera systems
        cameraConfig = CoreCams.get_config_info("cameras.ini")
        
        if(cameraConfig != None):
            self.cameras = CoreCams.ConstructCameraObjects(cameraConfig)
        else:
            raise ValueError("Camera config could not be found")

        #update status values consistently
        for cameraObject in self.cameras:
            Clock.schedule_interval(partial(self.update_button_color, cameraObject.name), 10)
            
        Clock.schedule_interval(partial(self.update_videostatus), 8)
        Clock.schedule_interval(partial(self.repeating_network_initiation), 120)


    def update_button_color(self, cam_id, dt):

        for index, cameraObject in enumerate(self.cameras):
            if(cameraObject.name == cam_id):
                cameraObject = CoreCams.testRTSP_Ping(cameraObject)
                self.cameras[index] = cameraObject

        new_color = self.get_cam_color(cam_id)
        cam_status_color=new_color
        for widget in self.walk():
            if getattr(widget, 'camera_id_string', None) == cam_id:
                widget.normal_color = new_color
        

    def repeating_network_initiation(self, dt):
        CoreCams.initializeInternalNetwork()
        print('re-initiated networking')

    def get_cam_info(self, cam_id):

        camIndex=0
        for index, cameraObject in enumerate(self.cameras):
            if(cameraObject.name == cam_id):
                return self.cameras[index].cam_status

        return "No Data"
        
    def get_cam_color(self, cam_id):
        
        camIndex=0
        for index, cameraObject in enumerate(self.cameras):
            if(cameraObject.name == cam_id):
                pickedCamera = cameraObject
                camIndex=index
            
        #if the cameras was not found in camera.ini, make it this unique color
        if(pickedCamera == None):
            self.cameras[camIndex].cam_status = "Camera Not Initialized"
            return [1, 1, 1, 1]

        if(pickedCamera.readytoload == False):
            self.cameras[camIndex].cam_status = "Camera Not Detected"
            return [0.515, 0.23, 0.215, 1]

        match str(pickedCamera.StatusValue):

            case "-3": # Camera has never recorded since first boot
                self.cameras[camIndex].cam_status = "Camera Pending Start"
                return [0.99, 0.69  , 0.14  , 1]
            
            case "-2": # unknown state
                self.cameras[camIndex].cam_status = "Camera Status Unknown"
                return [0.2 , 0.4   , 1     , 1]

            case "-1": # failure
                self.cameras[camIndex].cam_status = "Camera Recording FAILURE"
                return [1   , 0.2   , 0     , 1]

            case "0": #disconnected
                self.cameras[camIndex].cam_status = "Camera Disconnected"
                return [0.8 , 0.4   , 0.4   , 1]
            
            case "1": # currently recording
                self.cameras[camIndex].cam_status = "Camera Recording"
                return [0.52, 0.81  , 0.25  , 1]

            case "2": #recording completed (restarting)
                self.cameras[camIndex].cam_status = "Camera Recording Completed"
                return [1   , 0.5   , 0     , 1]

            case _: #default is -5, and gets overwritten quickly. This status means it's effectively stuck
                self.cameras[camIndex].cam_status = "Camera Not Initialized"
                return [0.75 , 0.75 , 0.75  , 1]
            
        #should never be here
        self.cameras[camIndex].cam_status = "Impossible Condition Detected"
        return [0, 0, 0, 1]


    def update_videostatus(self, dt):
        self.cameras=CoreCams.updateCameraStatus(self.cameras)
        if(self.selected_cam != None):
            self.cam_status = ("Status: " + self.selected_cam.cam_status)
        else:
            self.cam_status = "Please wait..."

    
    def toggle_layout(self,buttonType,screenid,pageid):

        # FIND PAGE IN pagesArray
        try:
            for pageObject in pagesArray:
                if((pageObject.name == str(pageid)) or (pageid=="All")):
                    if((pageObject.dynamic)):
                        #go through all menus that are not this one and minimize them
                        for menuid in pageObject.menus:

                            thisMenu = self.ids[menuid]
                            if(screenid == "All"): # close all screens (switching page usually)
                                anim = Animation(size_hint_x=0, opacity=0,disabled=True, d=0.01, t='out_quad')
                            else:
                                if((menuid == screenid)): 
                                    if thisMenu.size_hint_x > 0:
                                        anim = Animation(size_hint_x=0, opacity=0,disabled=True, d=0.3, t='out_quad')
                                    else:
                                        anim = Animation(size_hint_x=5, opacity=1,disabled=False, d=0.01, t='out_quad')        
                                else:
                                    anim = Animation(size_hint_x=0, opacity=0,disabled=True, d=0.3, t='out_quad')
                                
                            anim.start(thisMenu)
        except: #likely a page with no pageObject
            pass


        
        # SPECIFICALLY FOR CAMERA SCREEN, DISABLED NON SELECTED CAMERAS
        #--------------------------------------------------------------
        if(buttonType != None):
            cam = None
            try:
                cameraId = buttonType.camera_id_string
                # find camera item in self.cameras array
                for cameraObject in self.cameras:
                    if(cameraObject.name == cameraId):
                        cam = cameraObject        
                self.menu_text = cam.location
                self.selected_cam = cam

            except:
                pass #this was likely the close button being hit (has no id)


            extra = self.ids[screenid]
            
            if extra.size_hint_x > 0:
                anim = Animation(size_hint_x=0, opacity=0,disabled=True, d=0.3, t='out_quad')
                for widget in self.walk():
                    if widget.__class__.__name__ == "CameraButtons":
                        widget.opacity = 1
                        widget.disabled = False
            else:
                anim = Animation(size_hint_x=5, opacity=1,disabled=False, d=0.3, t='out_quad')
                for widget in self.walk():
                    if widget.__class__.__name__ == "CameraButtons":
                        if widget is not buttonType:
                            widget.opacity = 0
                            widget.disabled = True
                        buttonType.opacity=1
                        
            anim.start(extra)


            
class MainApp(App):
    
    carShineColorOffset = NumericProperty(0.5)
    carColor=ColorProperty([0.37, 0.37, 0.37, 1])  # Default to grey
    icons_visible = BooleanProperty(True)    
    
    #gif_handler = ObjectProperty(Image(source='loading.gif', anim_delay=0.1))
    def build(self):
        self.title = "CARPC SYSTEM"
        self.icon = 'icon.png' #window icon
        return MainLayout()
        
    def switch_screen(self, screen_name):
        sm = self.root.ids.screen_manager
        screen_order = ['cameras','about','music','knight','settings']

        self.root.toggle_layout(None,"All","All")
        
        current_index = screen_order.index(sm.current)
        target_index = screen_order.index(screen_name)

        direction = 'left' if target_index > current_index else 'right'
        sm.transition.direction = direction

        # Defer screen change to next frame (Linux fix)
        Clock.schedule_once(lambda dt: setattr(sm, 'current', screen_name), 0.05)

    def startcamPreview(self):
        print('starting cams')
        #CoreCams.initializeInternalNetwork()
        #self.capture = cv2.VideoCapture("/dev/video0")
                # Request resolution
        #self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        #self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        #self.capture.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*"MJPG"))
        #self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        #self.root.ids.camera_view.start(self.capture, fps=15)
        
        #self.capture = cv2.VideoCapture(
        #    "rtsp://cam3:test12345678@10.0.0.209:554/h264Preview_01_sub"
        #)
        #self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        #self.root.ids.camera_view2.start(self.capture, fps=15)
        
        #self.capture = cv2.VideoCapture(
         #   "rtsp://cam1:test12345678@10.0.0.207:554/h264Preview_01_sub"
        #)
        #self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Access widget created in kv
        #self.root.ids.camera_view3.start(self.capture, fps=15)

    def stopcamPreview(self):
        if self.capture:
            self.capture.release()

    def on_stop(self):
        if self.capture:
            self.capture.release()

    def on_start(self):
        self.startcamPreview()
    
    def exit(self):
        Clock.schedule_once(lambda dt: self.stop(), 0)

    def start_task(self):
        test()
        
if __name__ == "__main__":
    MainApp().run()
