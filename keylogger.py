from pynput import keyboard
import csv
import time
import sys, os


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.getcwd())
    return os.path.join(base_path, relative_path)


class KeyLogger:
    def __init__(self):
        self.path = "E:/Program Files/AuthenticationSystem/logged_keystrokes.csv"
        self.start_time = time.time()
        with open(resource_path(self.path), 'w', newline='') as file:
            self.keystrokes_file = csv.writer(file)
        with keyboard.Listener(
                on_press=self.pressed_key,
                on_release=self.released_key) as listener:
            listener.join()

    def pressed_key(self, key):
        with open(resource_path(self.path), 'a', newline='') as file:
            self.keystrokes_file = csv.writer(file)
            try:
                self.keystrokes_file.writerow(["pressed", str(key), time.time() - self.start_time])
            except UnicodeEncodeError:
                pass

    def released_key(self, key):
        with open(resource_path(self.path), 'a', newline='') as file:
            self.keystrokes_file = csv.writer(file)
            try:
                self.keystrokes_file.writerow(["released", str(key), time.time() - self.start_time])
            except UnicodeEncodeError:
                pass

        with open(resource_path(self.path)) as f:
            number_of_lines = sum(1 for line in f)
        if number_of_lines > 100:
            return False

# key_logger = KeyLogger()
