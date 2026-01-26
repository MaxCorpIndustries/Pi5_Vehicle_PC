

import threading
import sys
import os
import signal
import cv2
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

from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, SlideTransition

Window.borderless = True

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
    pass


class MainApp(App):

    def build(self):
        self.title = "CARPC SYSTEM"
        self.icon = 'icon.png'  # Set the icon path here
        #Builder.load_file("main.kv")
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
        self.capture.release()
        self.capture = cv2.VideoCapture("/dev/video0")
                # Request resolution
        #self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        #self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        #self.capture.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*"MJPG"))
        #self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.root.ids.camera_view.start(self.capture, fps=15)
        
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
