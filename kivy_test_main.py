import subprocess
import sys
import time

def launch_kivy_subprocess():
    # 'sys.executable' ensures the same Python interpreter is used
    command = [sys.executable, 'kivy_app.py']
    
    # Use Popen to run the process in the background without blocking the main script
    try:
        process = subprocess.Popen(command)
        print(f"Kivy subprocess launched with PID: {process.pid}")
        # You can interact with the process object (e.g., process.poll(), process.kill())
        return process
    except FileNotFoundError:
        print(f"Error: Could not find Python executable or kivy_app.py")
        print("Make sure Kivy is installed in the current environment.")
        return None

if __name__ == '__main__':
    print("Main script started.")
    kivy_process = launch_kivy_subprocess()
    
    if kivy_process:
        # Example of the main script continuing to run
        time.sleep(2) 
        print("Main script is still running while Kivy app is open.")
        
        # To wait for the process to finish if needed:
        # kivy_process.wait() 
        # print("Kivy subprocess finished.")
