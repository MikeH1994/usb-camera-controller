from pyusbcameraindex import enumerate_usb_video_devices_windows, USBCameraDevice
import cv2
import time
from collections import namedtuple
import sounddevice as sd
import threading


class CameraManager:
    def __init__(self):
        self.cameras = CameraManager.get_available_cameras(open_stream=True)
        self.camera_names = ["({}) {}".format(i, self.cameras[i].name) for i in range(len(self.cameras))]

    def get_camera_names(self):
        names = []
        for i, device in enumerate(self.cameras):
            names.append("({}) - {} ({}x())".format(i, device.name, device.size[1], device.size[0]))
        return names

    def get_image(self, index):
        for device in self.cameras:
            if index == device.index:
                ret, frame = device.device.read()
                if ret:
                    return frame
                else:
                    return None
        return None

    def get_all_images(self):
        images = []
        for device in self.cameras:
            ret, frame = device.device.read()
            if ret:
                images.append(frame)
            else:
                images.append(None)
        return images


    @staticmethod
    def camera_is_available(device_index):
        camera = cv2.VideoCapture(device_index)
        if not camera.isOpened():
            return False, None

        is_reading = camera.isOpened()
        w = camera.get(3)
        h = camera.get(4)
        if not is_reading:
            return False, None
        camera.release()
        return True, (int(h), int(w))

    @staticmethod
    def get_available_cameras(indices_to_ignore = None, open_stream=False):
        indices_to_ignore = [] if indices_to_ignore is None else indices_to_ignore
        listed_devices = enumerate_usb_video_devices_windows()
        available_devices = []
        for device in listed_devices:
            if device.index in indices_to_ignore:
                continue
            try:
                is_available, size = CameraManager.camera_is_available(device.index)
                stream = None
                if is_available:
                    if open_stream:
                        stream = cv2.VideoCapture(device.index)

                    available_device = USBCameraDevice(name=device.name, vid=device.vid, pid=device.pid, index=device.index,
                                                       path=device.path, size=size, device=stream, lock = threading.Lock())
                    available_devices.append(available_device)
            except Exception:
                pass
        return available_devices


if __name__ == "__main__":
    device_manager = CameraManager()
    devices = device_manager.cameras
    for device_ in devices:
        print(f"    {device_.index} = {device_.name} (VID={device_.vid}, PID={device_.pid}) res = {device_.size}")
