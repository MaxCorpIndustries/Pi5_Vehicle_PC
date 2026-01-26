

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
    capture = None
    fps = 30

    def start(self, capture, fps=30):
        self.capture = capture
        self.fps = fps
        Clock.schedule_interval(self.update, 1.0 / fps)

    def update(self, dt):
        if not self.capture:
            return

        ret, frame = self.capture.read()
        if ret:
            frame = cv2.flip(frame, 0)
            buf = frame.tobytes()

            texture = Texture.create(
                size=(frame.shape[1], frame.shape[0]),
                colorfmt='bgr'
            )
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.texture = texture

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

    def on_start(self):
        self.capture = cv2.VideoCapture(
            "/dev/video0"
        )
                # Request resolution
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 576)
        print('starting cams')
        # Access widget created in kv
        self.root.ids.camera_view.start(self.capture, fps=30)

    def on_stop(self):
        if self.capture:
            self.capture.release()
            
    def exit(self):
        Clock.schedule_once(lambda dt: self.stop(), 0)

    def start_task(self):
        test()
        
if __name__ == "__main__":
    MainApp().run()
