

import threading
import sys
import os
import signal
import cv2

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
    def start(self, source, fps=15, reconnect_delay=2.0):
        """
        source: RTSP url or /dev/videoX
        """
        self.source = source
        self.fps = fps
        self.reconnect_delay = reconnect_delay

        self.capture = None
        self.texture = None
        self.last_fail_time = 0
        self.connected = False

        self._event = Clock.schedule_interval(self.update, 1.0 / fps)

    def stop(self):
        if hasattr(self, "_event"):
            self._event.cancel()
        self._release()

    def _release(self):
        if self.capture:
            self.capture.release()
            self.capture = None
        self.connected = False

    def _connect(self):
        now = time.time()

        # Backoff so we don't hammer reconnects
        if now - self.last_fail_time < self.reconnect_delay:
            return False

        self.last_fail_time = now
        print("Connecting to camera...")

        self.capture = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)

        # RTSP stability flags
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not self.capture.isOpened():
            print("RTSP connect failed")
            self._release()
            return False

        print("Camera connected")
        self.connected = True
        return True

    def update(self, dt):
        # Ensure connection
        if not self.connected:
            self._connect()
            return

        ret, frame = self.capture.read()

        if not ret or frame is None:
            print("Frame read failed, reconnecting...")
            self._release()
            return

        h, w, _ = frame.shape

        if self.texture is None:
            self.texture = Texture.create(
                size=(w, h),
                colorfmt="bgr"
            )
            self.texture.flip_vertical()

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
        
        self.capture = cv2.VideoCapture(
            "/dev/video0"
        )
                # Request resolution
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 576)
        #self.capture.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*"MJPG"))
        #self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.root.ids.camera_view.start(self.capture, fps=15)
        
        self.capture = cv2.VideoCapture(
            "rtsp://cam3:test12345678@10.0.0.209:554/h264Preview_01_sub"
        )
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.root.ids.camera_view2.start(self.capture, fps=15)
        
        self.capture = cv2.VideoCapture(
            "rtsp://cam1:test12345678@10.0.0.207:554/h264Preview_01_sub"
        )
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Access widget created in kv
        self.root.ids.camera_view3.start(self.capture, fps=15)

    def on_stop(self):
        if self.capture:
            self.capture.release()
            
    def exit(self):
        Clock.schedule_once(lambda dt: self.stop(), 0)

    def start_task(self):
        test()
        
if __name__ == "__main__":
    MainApp().run()
