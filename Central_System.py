import CORE_WebcamRecording as cam
from kivy.app import App


class TestApp(App):
    pass

def main():
    print('started')
    cam.StartVideoProcess()
    TestApp().run()

# Run the main() function
if __name__ == '__main__':
    main()
