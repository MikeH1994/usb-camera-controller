import tkinter
import tkinter.filedialog
from tkinter import ttk
from typing import Tuple
from numpy.typing import NDArray
import numpy as np
from PIL import ImageTk, Image
from utils import resize_image
import threading
from typing import List
from camera_manager import CameraManager
from microphone_manager import MicrophoneManager


class GUIDevicePopup(tkinter.Frame):
    window_size: Tuple[int, int]

    def __init__(self, window: tkinter.Tk, names: List[str]):
        # Create and display a test window for viewing the menus
        super().__init__(window)
        # self.pack()
        self.window_size = (700, 900)
        self.window = window

        self.device_frame = tkinter.Frame(self.window, width=self.window_size[0],
                                          height=self.window_size[1])
        self.device_frame.grid(row=0, column=0, padx=10, pady=10)

        # create camera listbox and scrollbar
        self.device_listbox_frame = tkinter.Frame(self.device_frame, height=400)
        self.device_listbox_title = tkinter.Label(self.device_frame, text="Cameras")
        self.device_listbox_title.grid(row=0, column=0)
        self.device_listbox_frame.grid(row=1, column=0)
        self.device_selected_list = self.add_listbox(self.device_frame)

        self.add_buttons(self.device_listbox_frame, button_labels=["Add devices"], button_commands=[self.cb_add_device])

        for name in names:
            self.device_selected_list.insert(self.device_selected_list.size(), name)
        self.selected_indices = []

    def add_buttons(self, master, button_labels, button_commands):
        for i in range(len(button_labels)):
            button = tkinter.Button(master, text=button_labels[i], command=button_commands[i])
            button.grid(row=0, column=i)

    def add_listbox(self, master):
        frame = tkinter.Frame(master, height=800)
        frame.grid(row=0, column=0)
        listbox = tkinter.Listbox(frame, selectmode = "multiple")
        listbox.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
        scrollbar = tkinter.Scrollbar(frame)
        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.BOTH)
        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        return listbox

    def cb_add_device(self):
        self.selected_indices = self.device_selected_list.curselection()
        self.window.quit()


def run():
    names = ["Device 1", "Device 2", "Device 3"]
    root = tkinter.Tk()
    root.call('wm', 'attributes', '.', '-topmost', True)
    application = GUIDevicePopup(root, names)
    root.mainloop()
    print(application.selected_indices)


if __name__ == '__main__':
    run()
