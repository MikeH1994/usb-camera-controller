import numpy as np
import cv2
from tkinter import Tk, Label, Button, Frame, Scale, filedialog
import tkinter
import threading
import os
import pickle
import time
from datetime import datetime
from device_manager import DeviceManager


class GuiCheckbox:
    def __init__(self, master):
        self.master = master
        self.master.maxsize(900, 600)
        self.master.title("")
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        self.cameras = DeviceManager.get_available_cameras()

        self.frame = Frame(self.master)
        self.camera_frame = Frame(root, width=400, height=400, bg='grey')
        self.camera_frame.grid(row=0, column=0, padx=10, pady=5)
        self.camera_frame_title = Label(self.camera_frame, text="Cameras").grid(row=0, column=0, padx=5, pady=5)
        self.camera_checkbox_frame = Frame(self.camera_frame, width=400, height=400, bg='grey')
        self.camera_checkbox_frame.grid(row=1, column=0, padx=10, pady=5)

        for i, camera in enumerate(self.cameras):
            text = camera.name + "\n" + "({}, {})".format(camera.size[1], camera.size[0])
            button = tkinter.Checkbutton(self.camera_checkbox_frame, text=text,
                                         onvalue=1, offvalue=0, height=2, width=50)
            button.grid(row=1+i, column=0, padx=10, pady=5)

        self.microphone_frame = Frame(root, width=400, height=400, bg='grey')
        self.microphone_frame.grid(row=0, column=1, padx=10, pady=5)
        self.microphone_frame_title = Label(self.microphone_frame, text="Microphones").grid(row=0, column=0, padx=5, pady=5)
        self.microphone_checkbox_frame = Frame(self.microphone_frame, width=400, height=400, bg='grey')
        self.microphone_checkbox_frame.grid(row=1, column=0, padx=10, pady=5)
        self.microphones = DeviceManager.get_available_microphones()
        for i, microphone in enumerate(self.microphones):
            text = microphone.name
            button = tkinter.Checkbutton(self.microphone_checkbox_frame, text=text,
                                         onvalue=1, offvalue=0, height=2, width=50)
            button.grid(row=1+i, column=0, padx=10, pady=5)


    def on_close(self):
        pass

    def initialise(self):
        pass

    def get_choice(self):
        return


if __name__ == '__main__':
    root = tkinter.Tk()
    root.call('wm', 'attributes', '.', '-topmost', True)
    application = GuiCheckbox(root)
    root.mainloop()
