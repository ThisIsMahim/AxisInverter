import pyautogui
import json
import os
from time import sleep
from pynput import keyboard
from pynput import mouse
from threading import Thread


class AxisInverter:
    def __init__(self):
        os.system("title AxisInverter")
        if os.path.isfile("config.json"):
            with open("config.json", "r+") as config_file:
                file_content = config_file.read()
                banned_keys: dict = json.loads(file_content)
        else:
            with open("config.json", "w") as config_file_create:
                banned_keys = {"banned_keys": ["w", "a", "s", "d"]}
                json.dump(banned_keys, config_file_create)
        # List of keys that cannot be the switch.
        # I'm blocking "w", "a", "s", "d" just because they are used in games for movement.
        # Feel free to change it.
        self.parsed_keys = []
        for key in banned_keys["banned_keys"]:
            self.parsed_keys.append(self.key_parser(key))
        self.mouse = mouse.Controller()
        self.switch_set = False
        self.inverted = False
        self.thread = None
        self.first_usage = True
        self.switch = None
        self.mouse = mouse.Controller()
        self.minx, self.miny = (0, 0)
        self.maxx, self.maxy = pyautogui.size()  # Getting the max x and max y of your screen.
        print("Press the key to choose a switch...")

        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as keyboard_listener:
            keyboard_listener.join()

    @staticmethod
    def key_parser(key: str):
        parsed_key = keyboard.KeyCode.from_char(key)
        return parsed_key

    @staticmethod
    def equals(n1: int, n2: int) -> bool:
        if abs(n1 - n2) < 3:
            return True
        else:
            return False

    def on_press(self, key):
        if not self.switch_set:
            try:
                if key in self.parsed_keys:
                    print("{0} cannot be a switch".format(key.char.upper()))
                    print("Choose another key...")
                else:
                    print("{0} is your switch button.".format(key.char.upper()))
                    self.switch_set = True
                    self.switch = key
                    self.first_usage = True
            except AttributeError:  # Special keys like shift aren't supported.
                print("Choose another key, this one is not supported.")

    def on_release(self, key):
        if self.switch_set:
            if key == self.switch:
                if self.first_usage:  # It won't invert our mouse automatically after we choose the switch.
                    self.inverted = False
                    self.first_usage = False
                    print("Press {0} to invert your mouse movement".format(key.char.upper()))
                else:
                    if not self.inverted:
                        self.inverted = True
                        print("Your mouse movement is now inverted.")
                        # Threading is used to manage the keyboard listener AND to do the inverting loop.
                        # If we wouldn't use threading, we wouldn't be able to switch the inversion with a key.
                        self.thread = Thread(target=self.inversion)
                        self.thread.daemon = True
                        self.thread.start()
                    else:
                        self.inverted = False
                        # If we press the switch button again, mouse movement will be back to normal.
                        print("Your mouse movement is back to normal.")
                        if self.thread.is_alive():
                            self.thread.join()

    def inversion(self):
        while self.inverted:
            x1, y1 = pyautogui.position()
            # Increase this value if you want your computer to use less resources.
            # If you want the movement to be smooth, keep this value low, for example 0.001
            sleep(0.001)
            x2, y2 = pyautogui.position()
            if self.equals(x1, self.maxx):
                x1 = x1 - 2
            if self.equals(x2, self.maxx):
                x2 = x2 - 2
            if self.equals(y1, self.maxy):
                y1 = y1 - 2
            if self.equals(y2, self.maxy):
                y2 = y2 - 2
            if self.equals(x1, self.minx):
                x1 = x1 + 2
            if self.equals(x2, self.minx):
                x2 = x2 + 2
            if self.equals(y1, self.miny):
                y1 = y1 + 2
            if self.equals(y2, self.miny):
                y2 = y2 + 2
            dx = x2 - x1
            dy = y2 - y1
            self.mouse.position = (x1 - dx, y1 - dy)


AxisInverter()
