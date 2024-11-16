import pyautogui
import json
import os
from time import sleep
from pynput import keyboard, mouse
from threading import Thread
import tkinter as tk
from tkinter import messagebox, simpledialog
import logging

class AxisInverter:
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.init_variables()
        self.create_gui()
        self.start_listeners()

    def setup_logging(self):
        logging.basicConfig(filename='axis_inverter.log', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def load_config(self):
        default_config = {
            "banned_keys": ["w", "a", "s", "d"],
            "inversion_speed": 0.001,
            "hotkey": "f8",
            "inversion_zone": {"x1": 0, "y1": 0, "x2": 1920, "y2": 1080},
            "invert_x": True,
            "invert_y": True,
            "profiles": {}
        }
        try:
            with open("config.json", "r") as config_file:
                self.config = json.load(config_file)
        except FileNotFoundError:
            self.config = default_config
        
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value
        
        self.save_config()

    def save_config(self):
        with open("config.json", "w") as config_file:
            json.dump(self.config, config_file, indent=4)

    def init_variables(self):
        self.mouse_controller = mouse.Controller()
        self.inverted = False
        self.inversion_thread = None
        self.minx, self.miny = (0, 0)
        self.maxx, self.maxy = pyautogui.size()
        self.overlay = None

    def create_gui(self):
        self.window = tk.Tk()
        self.window.title("Mouse Axis Inverter")
        self.window.geometry("600x800")
        
        self.create_widgets()
        self.window.protocol("WM_DELETE_WINDOW", self.exit_app)

    def create_widgets(self):
        tk.Label(self.window, text="Enhanced Axis Inverter", font=("Helvetica", 16)).pack(pady=10)

        self.status_var = tk.StringVar(value="Status: Normal")
        tk.Label(self.window, textvariable=self.status_var, font=("Helvetica", 12)).pack(pady=10)

        self.toggle_button = tk.Button(self.window, text="Toggle Inversion", command=self.toggle_inversion)
        self.toggle_button.pack(pady=10)

        self.speed_scale = tk.Scale(
            self.window, from_=0.0001, to=0.01, orient=tk.HORIZONTAL, length=200,
            command=self.update_speed, resolution=0.0001
        )
        self.speed_scale.set(self.config["inversion_speed"])
        self.speed_scale.pack(pady=10)
        tk.Label(self.window, text="Inversion Speed").pack()

        self.hotkey_var = tk.StringVar(value=self.config["hotkey"])
        tk.Label(self.window, text="Hotkey:").pack(pady=(10, 0))
        self.hotkey_entry = tk.Entry(self.window, textvariable=self.hotkey_var)
        self.hotkey_entry.pack()
        tk.Button(self.window, text="Set Hotkey", command=self.set_hotkey).pack(pady=(0, 10))

        self.invert_x_var = tk.BooleanVar(value=self.config["invert_x"])
        self.invert_y_var = tk.BooleanVar(value=self.config["invert_y"])
        tk.Checkbutton(self.window, text="Invert X axis", variable=self.invert_x_var, command=self.update_invert_axes).pack()
        tk.Checkbutton(self.window, text="Invert Y axis", variable=self.invert_y_var, command=self.update_invert_axes).pack()

        tk.Button(self.window, text="Set Inversion Zone", command=self.set_inversion_zone).pack(pady=10)

        self.profile_var = tk.StringVar()
        tk.Label(self.window, text="Profile:").pack(pady=(10, 0))
        self.profile_entry = tk.Entry(self.window, textvariable=self.profile_var)
        self.profile_entry.pack()
        tk.Button(self.window, text="Save Profile", command=self.save_profile).pack(pady=(0, 5))
        tk.Button(self.window, text="Load Profile", command=self.load_profile).pack()

        self.quit_button = tk.Button(self.window, text="Exit", command=self.exit_app)
        self.quit_button.pack(pady=20)

    def start_listeners(self):
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.keyboard_listener.start()

    def on_key_press(self, key):
        try:
            if key.char.lower() == self.config["hotkey"].lower():
                self.toggle_inversion()
        except AttributeError:
            pass

    def toggle_inversion(self):
        self.inverted = not self.inverted
        if self.inverted:
            self.status_var.set("Status: Inverted")
            self.inversion_thread = Thread(target=self.inversion_loop)
            self.inversion_thread.daemon = True
            self.inversion_thread.start()
            self.show_overlay()
            logging.info("Inversion started")
        else:
            self.status_var.set("Status: Normal")
            self.hide_overlay()
            logging.info("Inversion stopped")

    def inversion_loop(self):
        while self.inverted:
            x1, y1 = pyautogui.position()
            sleep(self.config["inversion_speed"])
            x2, y2 = pyautogui.position()
            x1, y1 = self.adjust_coordinates(x1, y1)
            x2, y2 = self.adjust_coordinates(x2, y2)
            dx = x2 - x1 if self.config["invert_x"] else 0
            dy = y2 - y1 if self.config["invert_y"] else 0
            
            zone = self.config["inversion_zone"]
            if zone["x1"] <= x1 <= zone["x2"] and zone["y1"] <= y1 <= zone["y2"]:
                self.mouse_controller.position = (x1 - dx, y1 - dy)

    def adjust_coordinates(self, x, y):
        if self.equals(x, self.maxx): x -= 2
        if self.equals(y, self.maxy): y -= 2
        if self.equals(x, self.minx): x += 2
        if self.equals(y, self.miny): y += 2
        return x, y

    @staticmethod
    def equals(n1, n2):
        return abs(n1 - n2) < 3

    def update_speed(self, value):
        self.config["inversion_speed"] = float(value)
        self.save_config()

    def set_hotkey(self):
        new_hotkey = self.hotkey_var.get().lower()
        if new_hotkey not in self.config["banned_keys"]:
            self.config["hotkey"] = new_hotkey
            self.save_config()
            messagebox.showinfo("Hotkey Set", f"Hotkey set to: {new_hotkey.upper()}")
        else:
            messagebox.showwarning("Invalid Hotkey", f"{new_hotkey.upper()} is not allowed as a hotkey.")

    def update_invert_axes(self):
        self.config["invert_x"] = self.invert_x_var.get()
        self.config["invert_y"] = self.invert_y_var.get()
        self.save_config()

    def set_inversion_zone(self):
        zone = simpledialog.askstring("Inversion Zone", "Enter zone as x1,y1,x2,y2:")
        if zone:
            try:
                x1, y1, x2, y2 = map(int, zone.split(','))
                self.config["inversion_zone"] = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
                self.save_config()
                messagebox.showinfo("Inversion Zone Set", f"Zone set to: {x1},{y1},{x2},{y2}")
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter four integers separated by commas.")

    def save_profile(self):
        profile_name = self.profile_var.get()
        if profile_name:
            self.config["profiles"][profile_name] = {
                "inversion_speed": self.config["inversion_speed"],
                "invert_x": self.config["invert_x"],
                "invert_y": self.config["invert_y"],
                "inversion_zone": self.config["inversion_zone"]
            }
            self.save_config()
            messagebox.showinfo("Profile Saved", f"Profile '{profile_name}' saved successfully.")

    def load_profile(self):
        profile_name = self.profile_var.get()
        if profile_name in self.config["profiles"]:
            profile = self.config["profiles"][profile_name]
            self.config["inversion_speed"] = profile["inversion_speed"]
            self.config["invert_x"] = profile["invert_x"]
            self.config["invert_y"] = profile["invert_y"]
            self.config["inversion_zone"] = profile["inversion_zone"]
            self.speed_scale.set(self.config["inversion_speed"])
            self.invert_x_var.set(self.config["invert_x"])
            self.invert_y_var.set(self.config["invert_y"])
            self.save_config()
            messagebox.showinfo("Profile Loaded", f"Profile '{profile_name}' loaded successfully.")
        else:
            messagebox.showerror("Profile Not Found", f"Profile '{profile_name}' does not exist.")

    def show_overlay(self):
        if not self.overlay:
            self.overlay = tk.Toplevel(self.window)
            self.overlay.overrideredirect(True)
            self.overlay.attributes("-topmost", True)
            self.overlay.attributes("-alpha", 0.5)
            label = tk.Label(self.overlay, text="Inverted", bg="red", fg="white")
            label.pack()
        self.overlay.geometry("+0+0")
        self.overlay.deiconify()

    def hide_overlay(self):
        if self.overlay:
            self.overlay.withdraw()

    def exit_app(self):
        self.inverted = False
        if self.inversion_thread and self.inversion_thread.is_alive():
            self.inversion_thread.join()
        self.keyboard_listener.stop()
        self.window.destroy()
        logging.info("Application closed")

if __name__ == "__main__":
    app = AxisInverter()
    app.window.mainloop()