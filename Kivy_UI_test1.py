# main.py (modified to use the .kv file)
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
# The MyRootLayout class defined in the .kv file needs to be defined in Python too
class MyRootLayout(BoxLayout):
    pass

class MyApp(App):
    def build(self):
        # Kivy will automatically load 'my.kv' and return the root widget
        return MyRootLayout()

if __name__ == '__main__':
    MyApp().run()

