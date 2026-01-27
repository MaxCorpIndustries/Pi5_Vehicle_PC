

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
from kivy.properties import ListProperty, StringProperty, BooleanProperty
from kivy.factory import Factory

from functools import partial

from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.uix.button import Button

Window.borderless = True

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
        for a in self.cameras:
            Clock.schedule_interval(partial(self.update_button_color, a.name), 2)
            
        Clock.schedule_interval(partial(self.update_videostatus, self.cameras), 5)

    def update_button_color(self, cam_id, dt):

        for index, cameraObject in enumerate(self.cameras):
            if(cameraObject.name == cam_id):
                cameraObject = CoreCams.testRTSP_Ping(cameraObject)
                self.cameras[index] = cameraObject
        
        new_color = self.get_cam_color(cam_id)        
        for widget in self.walk():
            if getattr(widget, 'camera_id_string', None) == cam_id:
                widget.normal_color = new_color

    def update_videostatus(self, cameraArray, dt):
        self.cameras=CoreCams.updateCameraStatus(cameraArray)
        
                
    def get_cam_color(self, cam_id):
        
        # find camera item in self.cameras array
        for cameraObject in self.cameras:
            if(cameraObject.name == cam_id):
                pickedCamera = cameraObject
            
        #if the cameras was not found in camera.ini, make it this unique color
        if(pickedCamera == None):
            return [1, 1, 1, 1]

        if(pickedCamera.readytoload == False):
            return [0.515, 0.23, 0.215, 1]
        
        match str(pickedCamera.StatusValue):
            
            case "-2": # unknown state
                return [0.2 , 0.4   , 1     , 1]

            case "-1": # failure
                return [1   , 0.2   , 0     , 1]

            case "0": #disconnected
                return [0.4 , 0.4   , 0.4   , 1]  
            
            case "1": # currently recording
                return [0   , 1     , 0     , 1]

            case "2": #recording completed (restarting)
                return [1   , 0.5   , 0     , 1]

            case _:
                return [0.75 , 0.75   , 0.75   , 1]
            
        #should never be here
        return [0, 0, 0, 1]

    
    def toggle_layout(self,buttonType):

        try:
            cameraId = buttonType.camera_id_string
            # find camera item in self.cameras array
            for cameraObject in self.cameras:
                if(cameraObject.name == cameraId):
                    cam = cameraObject        
            self.menu_text = cam.name
        except:
            pass #this was likely the close button being hit (has no id)
            
        extra = self.ids.extra_layout
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
    pass


class MainApp(App):

    icons_visible = BooleanProperty(True)
    
    def build(self):
        self.title = "CARPC SYSTEM"
        self.icon = 'icon.png' #window icon
        return MainLayout()
        
    def switch_screen(self, screen_name):
        sm = self.root.ids.screen_manager
        screen_order = ['cameras', 'settings', 'about']

        current_index = screen_order.index(sm.current)
        target_index = screen_order.index(screen_name)

        direction = 'left' if target_index > current_index else 'right'
        sm.transition.direction = direction

        # Defer screen change to next frame (Linux fix)
        Clock.schedule_once(lambda dt: setattr(sm, 'current', screen_name), 0)

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
