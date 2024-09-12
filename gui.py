import tkinter
import tkinter.filedialog
from tkinter import ttk
from typing import Tuple
from numpy.typing import NDArray
import numpy as np
from PIL import ImageTk, Image
from utils import resize_image
import threading
from gui_device_popup import GUIDevicePopup
from camera_manager import CameraManager
from microphone_manager import MicrophoneManager
from camera_writer import CameraWriter
from microphone_writer import MicrophoneWriter
from typing import List
import time
import cv2
from tkinter import simpledialog, messagebox
from tkinter import filedialog
import os


class GUI:
    displayed_image_size: Tuple[int, int]

    def __init__(self, window: tkinter.Tk):
        # Create and display a test window for viewing the menus
        self.camera_manager = CameraManager()
        self.microphone_manager = MicrophoneManager()
        self.window = window
        self.camera_indices: List[int] = []  # list of indices for the cameras in camera manager
        self.microphone_indices: List[int] = []  # list of microphones for the microphone manager
        self.running = True
        self.writing_data = False
        self.modifying_devices = False

        self.camera_lock = threading.Lock()
        self.microphone_lock = threading.Lock()
        self.image_data_lock = threading.Lock()

        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.last_mousepos = (0, 0)
        self.displayed_image_size = (360, 480)
        self.default_image = np.zeros(self.displayed_image_size, dtype=np.uint8)

        # Create left and right frames
        self.frame_tl = tkinter.Frame(self.window, width=self.displayed_image_size[1],
                                      height=self.displayed_image_size[0],
                                      bg='grey')
        self.frame_tl.grid(row=0, column=0, padx=10, pady=10)
        self.frame_tr = tkinter.Frame(self.window, width=200,
                                      height=self.displayed_image_size[0],
                                      bg='grey')
        self.frame_tr.grid(row=0, column=1, padx=10, pady=10)
        self.frame_br = tkinter.Frame(self.window, width=50, height=50, bg='grey')
        self.frame_br.grid(row=1, column=1, padx=10, pady=10)

        self.image_label = tkinter.Label(master=self.frame_tl)
        self.image_label.pack(side=tkinter.TOP, fill=tkinter.BOTH)
        self.camera_selected_scrollbar = tkinter.Scale(self.frame_tl, from_=0, to=0, orient=tkinter.HORIZONTAL,
                                                       resolution=1, command=self.cb_camera_scrollbar_changed)
        self.camera_selected_scrollbar.pack(side=tkinter.BOTTOM, fill=tkinter.BOTH)

        # create tabs
        self.tabs = ttk.Notebook(self.frame_tr, height=self.displayed_image_size[0]-23)
        self.cameras_tab = tkinter.Frame(self.tabs, width=200)
        self.microphones_tab = tkinter.Frame(self.tabs, width=200)
        self.targets_tab = tkinter.Frame(self.tabs, width=200)
        self.tabs.add(self.cameras_tab, text="cameras")
        self.tabs.add(self.microphones_tab, text="microphones")
        self.tabs.pack()

        # create camera listbox and scrollbar
        self.camera_listbox_frame = tkinter.Frame(self.cameras_tab, height=400)
        self.camera_listbox_frame.grid(row=0, column=0)
        self.camera_selected_list = self.add_listbox(self.camera_listbox_frame)

        # create camera buttons
        self.camera_options_frame = tkinter.Frame(self.cameras_tab)
        self.camera_options_frame.grid(row=1, column=0)
        self.add_buttons(self.camera_options_frame, button_labels=["Add", "Rename", "Remove"],
                         button_commands=[self.cb_add_camera, self.cb_rename_camera, self.cb_remove_camera])

        # create object listbox and scrollbar
        self.microphone_listbox_frame = tkinter.Frame(self.microphones_tab, height=400)
        self.microphone_listbox_frame.grid(row=0, column=0)
        self.microphone_selected_list = self.add_listbox(self.microphone_listbox_frame)

        # create object buttons
        self.microphone_options_frame = tkinter.Frame(self.microphones_tab)
        self.microphone_options_frame.grid(row=1, column=0)
        self.add_buttons(self.microphone_options_frame, button_labels=["Add", "Rename", "Remove"],
                         button_commands=[self.cb_add_microphone, self.cb_rename_microphone, self.cb_remove_microphone])

        self.data_capture_button = tkinter.Button(self.frame_br, text="Start", command=self.cb_data_capture)
        self.data_capture_button.grid(row=0, column=0)

        self.camera_selected_list.bind("<<ListboxSelect>>", self.cb_camera_listbox_changed)  # add callback
        self.update_camera_scrollbar()

        self.image_changed = True
        self.last_images = []

        self.image_drawing_thread = threading.Thread(target=self.draw_image_loop)
        self.image_capture_thread = threading.Thread(target=self.capture_image_loop)
        self.write_data_thread = None

        self.image_drawing_thread.start()
        self.image_capture_thread.start()

    def on_close(self):
        self.running = False
        if self.writing_data:
            self.writing_data = False
            if self.write_data_thread is not None:
                self.write_data_thread.join()
        if self.image_capture_thread.is_alive():
            self.image_capture_thread.join(timeout=2)
        if self.image_drawing_thread.is_alive():
            self.image_drawing_thread.join(timeout=2)
        self.window.quit()
        self.window.destroy()

    def cb_data_capture(self):
        if self.writing_data:
            self.writing_data = False
            if self.write_data_thread is not None:
                self.write_data_thread.join()
        else:
            if len(self.camera_indices) + len(self.microphone_indices) == 0:
                messagebox.showerror("Error", "Add a device before beginnning capture")
                return

            output_folderpath = filedialog.askdirectory()
            if output_folderpath is None or output_folderpath == "":
                return

            if len(os.listdir(output_folderpath)) != 0:
                messagebox.showerror("Error", "Please select an empty folder")
                return


            frame_rate = simpledialog.askfloat(title="Frame rate", prompt="Enter frame rate", initialvalue=20.0)
            if frame_rate is None:
                return

            if frame_rate < 0.0:
                messagebox.showerror("Error", "Frame rate must be positive")
                return

            start = messagebox.askokcancel(title="Start Capture?", message="Start capture?")

            if not start:
                return

            self.write_data_thread = threading.Thread(target=self.write_data_loop, args=(output_folderpath, frame_rate))
            self.write_data_thread.start()
            self.writing_data = True

        if self.writing_data:
            self.data_capture_button.config(text="Stop")
        else:
            self.data_capture_button.config(text="Start")

    def cb_camera_scrollbar_changed(self, i):
        i = int(i)
        if i < self.camera_selected_list.size():
            self.camera_selected_list.selection_clear(0, tkinter.END)
            self.camera_selected_list.selection_set(i)
        self.image_changed = True

    # noinspection PyMethodMayBeStatic
    def add_buttons(self, master, button_labels, button_commands):
        for i in range(len(button_labels)):
            button = tkinter.Button(master, text=button_labels[i], command=button_commands[i])
            button.grid(row=0, column=i)

    # noinspection PyMethodMayBeStatic
    def add_listbox(self, master):
        frame = tkinter.Frame(master, height=400)
        frame.grid(row=0, column=0)
        listbox = tkinter.Listbox(frame)
        listbox.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
        scrollbar = tkinter.Scrollbar(frame)
        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.BOTH)
        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        return listbox

    def update_camera_scrollbar(self):
        max_n = max(len(self.camera_indices) - 1, 0)
        self.camera_selected_scrollbar.configure(to=max_n)
        n = min(self.get_camera_index(), max_n)
        self.camera_selected_scrollbar.set(n)
        if n < self.camera_selected_list.index("end"):
            self.camera_selected_list.selection_clear(0, tkinter.END)  # clear all selections
            self.camera_selected_list.selection_set(n)  # set the current selection
        self.image_changed = True

    def update_camera_listbox_selection(self, n=None):
        n = self.get_camera_index() if n is None else n

        if n == -1:
            return

        if n < self.camera_selected_list.index("end"):
            self.camera_selected_list.selection_clear(0, tkinter.END)
            self.camera_selected_list.selection_set(n)

    def update_listboxes(self):
        self.camera_selected_list.delete(0, tkinter.END)
        self.microphone_selected_list.delete(0, tkinter.END)

        for i in self.camera_indices:
            self.camera_selected_list.insert("end", self.camera_manager.camera_names[i])

        for i in self.microphone_indices:
            self.microphone_selected_list.insert("end", self.microphone_manager.microphone_names[i])

        self.update_camera_listbox_selection(self.get_camera_index())

    def cb_camera_listbox_changed(self, event):
        selection = event.widget.curselection()
        if len(selection) > 0:
            self.camera_selected_scrollbar.set(selection[0])

    def cb_add_camera(self):
        if self.modifying_devices or self.writing_data:
            return

        self.modifying_devices = True

        root = tkinter.Tk()
        n = len(self.camera_manager.camera_names)
        indices_to_display = [i for i in range(n) if i not in self.camera_indices]
        names = [self.camera_manager.camera_names[i] for i in indices_to_display]
        popup = GUIDevicePopup(root, names)
        root.call('wm', 'attributes', '.', '-topmost', True)
        root.mainloop()
        selected_indices = [indices_to_display[i] for i in popup.selected_indices]

        if len(selected_indices) != 0:
            self.add_cameras(selected_indices)
        self.update_camera_scrollbar()
        self.modifying_devices = False
        self.image_changed = True

    def cb_rename_camera(self):
        if self.modifying_devices or self.writing_data:
            return

        self.modifying_devices = True
        selection = self.camera_selected_list.curselection()
        if len(selection) > 0:
            i = self.camera_indices[selection[0]]
            old_name = self.camera_manager.camera_names[i]
            new_name = tkinter.simpledialog.askstring(title="Rename camera", prompt="Rename camera",
                                                      initialvalue=old_name)

            if new_name == old_name or new_name is None:
                pass
            elif new_name == "":
                messagebox.showerror("Error", "Cannot use empty name")
            elif new_name in self.camera_manager.camera_names:
                messagebox.showerror("Error", "Name already exists in camera names")
            else:
                self.camera_manager.camera_names[i] = new_name
                self.update_listboxes()
        self.modifying_devices = False

    def cb_remove_camera(self):
        if self.modifying_devices or self.writing_data:
            return

        self.modifying_devices = True
        selection = self.camera_selected_list.curselection()
        if len(selection) > 0:
            i = selection[0]
            self.camera_indices.pop(i)
            self.camera_selected_list.delete(i)
            self.update_camera_scrollbar()
            self.update_camera_listbox_selection()
        self.modifying_devices = False

    def cb_add_microphone(self):
        if self.modifying_devices or self.writing_data:
            return

        self.modifying_devices = True
        self.microphone_lock.acquire()
        root = tkinter.Tk()
        n = len(self.microphone_manager.microphone_names)
        indices_to_display = [i for i in range(n) if i not in self.microphone_indices]
        names = [self.microphone_manager.microphone_names[i] for i in indices_to_display]
        popup = GUIDevicePopup(root, names)
        root.call('wm', 'attributes', '.', '-topmost', True)
        root.mainloop()
        selected_indices = [indices_to_display[i] for i in popup.selected_indices]
        self.modifying_devices = False
        self.microphone_lock.release()
        self.add_microphones(selected_indices)

    def cb_rename_microphone(self):
        if self.modifying_devices or self.writing_data:
            return
        self.modifying_devices = True
        selection = self.microphone_selected_list.curselection()
        if len(selection) > 0:
            i = self.microphone_indices[selection[0]]
            old_name = self.microphone_manager.microphone_names[i]
            new_name = tkinter.simpledialog.askstring(title="Rename microphone", prompt="Rename microphone",
                                                      initialvalue=old_name)

            if new_name == old_name or new_name is None:
                pass
            elif new_name == "":
                messagebox.showerror("Error", "Cannot use empty name")
            elif new_name in self.microphone_manager.microphone_names:
                messagebox.showerror("Error", "Name already exists in microphone names")
            else:
                self.microphone_manager.microphone_names[i] = new_name
                self.update_listboxes()
        self.modifying_devices = False

    def cb_remove_microphone(self):
        if self.modifying_devices or self.writing_data:
            return
        self.modifying_devices = True
        selection = self.microphone_selected_list.curselection()
        if len(selection) > 0:
            i = selection[0]
            self.microphone_indices.pop(i)
            self.microphone_selected_list.delete(i)
        self.modifying_devices = False

    def get_camera_index(self):
        if len(self.camera_indices) == 0:
            return -1
        return self.camera_selected_scrollbar.get()

    def add_cameras(self, device_indices: List[int]):
        self.camera_lock.acquire()
        for i in device_indices:
            if i not in self.camera_indices:
                self.camera_indices.append(i)
        self.camera_lock.release()
        self.update_listboxes()
        self.image_changed = True

    def add_microphones(self, device_indices: List[int]):
        self.microphone_lock.acquire()
        for i in device_indices:
            if i not in self.microphone_indices:
                self.microphone_indices.append(i)
        self.microphone_lock.release()
        self.update_listboxes()
        self.image_changed = True

    def draw_image_loop(self):
        while self.running:
            if self.image_changed:
                camera_index = self.get_camera_index()
                if camera_index == -1 or len(self.camera_indices) == 0:
                    self.update_image_label(self.default_image)
                    time.sleep(0.01)
                    continue

                if camera_index >= len(self.last_images):
                    self.update_image_label(self.default_image)
                    time.sleep(0.01)
                    continue

                self.image_data_lock.acquire()
                image = cv2.cvtColor(self.last_images[camera_index], cv2.COLOR_BGR2RGB)
                self.image_changed = False
                self.image_data_lock.release()

                image_resized = resize_image(image, self.displayed_image_size)
                self.update_image_label(image_resized)
            time.sleep(0.01)

    def capture_image_loop(self):
        while self.running:
            images = []

            self.camera_lock.acquire()
            if len(self.camera_indices) == 0:
                self.camera_lock.release()
                continue

            for camera_index in self.camera_indices:
                camera = self.camera_manager.cameras[camera_index]
                camera.lock.acquire()
                ret, frame = camera.device.read()
                camera.lock.release()
                if ret:
                    images.append(frame)
                else:
                    images.append(None)
            self.camera_lock.release()

            self.image_data_lock.acquire()
            self.image_changed = True
            self.last_images = images
            self.image_data_lock.release()
            time.sleep(0.01)

    def write_data_loop(self, output_folderpath, frame_rate):
        if self.writing_data:
            return

        writers = []

        for camera_index in self.camera_indices:
            device = self.camera_manager.cameras[camera_index]
            name = self.camera_manager.camera_names[camera_index]
            writers.append(CameraWriter(device, output_folderpath, frame_rate, name=name))

        for microphone_index in self.microphone_indices:
            device = self.microphone_manager.microphones[microphone_index]
            name = self.microphone_manager.microphone_names[microphone_index]
            writers.append(MicrophoneWriter(device, output_folderpath, name=name))

        for w in writers:
            w.start()

        while self.writing_data:
            time.sleep(0.005)

        for w in writers:
            w.stop()

    def update_image_label(self, image: NDArray):
        image = resize_image(image, self.displayed_image_size)
        image = ImageTk.PhotoImage(image=Image.fromarray(image))
        self.image_label.configure(image=image)
        self.image_label.img = image


def run():
    root = tkinter.Tk()
    root.call('wm', 'attributes', '.', '-topmost', True)
    GUI(root)
    root.mainloop()


if __name__ == '__main__':
    run()
