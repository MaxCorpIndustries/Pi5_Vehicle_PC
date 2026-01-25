from kivy.app import App
from kivy.lang import Builder
import threading
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.config import Config

import sys
import os
import signal

Config.set('graphics', 'width', '1024')
Config.set('graphics', 'height', '600')


def test():
    pid = 12345 # Replace with the actual Process ID (PID)
    os.system(f'taskkill /F /PID {pid}')

class MainLayout(BoxLayout):
    def exit(self):
        Clock.schedule_once(lambda dt: self.stop(), 0)

    def start_task(self):
        test()
        
    pass


class MainApp(App):
    def build(self):
        
        #Builder.load_file("main.kv")
        return MainLayout()


if __name__ == "__main__":
    MainApp().run()
