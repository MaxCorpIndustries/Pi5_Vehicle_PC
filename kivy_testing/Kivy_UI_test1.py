from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
import sys

class KivyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        label = Label(text="Kivy UI running in a subprocess!")
        close_button = Button(text="Close Kivy App")
        close_button.bind(on_press=self.stop)
        layout.add_widget(label)
        layout.add_widget(close_button)
        return layout

if __name__ == '__main__':
    KivyApp().run()
