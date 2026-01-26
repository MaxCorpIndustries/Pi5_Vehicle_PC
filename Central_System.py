

import threading
import sys
import os
import signal

from kivy.config import Config
Config.set('graphics', 'width', '1024')
Config.set('graphics', 'height', '600')
#Config.set('graphics', 'fullscreen', 'auto')


from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.app import App
from kivy.lang import Builder

Window.borderless = True


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

    def exit(self):
        Clock.schedule_once(lambda dt: self.stop(), 0)

    def start_task(self):
        test()
        
if __name__ == "__main__":
    MainApp().run()
