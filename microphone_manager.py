from pyusbcameraindex import enumerate_usb_video_devices_windows,USBCameraDevice
import cv2
import time
from collections import namedtuple
import sounddevice as sd

MicrophoneDevice = namedtuple('MicrophoneDevice', 'name index samplerate channels')


class MicrophoneManager:
    def __init__(self):
        self.microphones = MicrophoneManager.get_available_microphones()
        self.microphone_names = ["({}) {}".format(i, self.microphones[i].name) for i in range(len(self.microphones))]

    @staticmethod
    def get_available_microphones(host_api=0, open_stream = False):
        found_devices = []
        found_devices_names = []
        all_input_devices = [d for d in sd.query_devices() if d["max_input_channels"] > 0]

        for device in all_input_devices:
            name = device["name"]
            index = device["index"]
            sample_rate = device["default_samplerate"]

            if host_api is not None and device["hostapi"] != host_api:
                continue
            if name == "Microsoft Sound Mapper - Input":
                continue
            if name in found_devices_names:
                continue
            channels = 1
            found_devices.append(MicrophoneDevice(name=name, index=index, samplerate=sample_rate, channels=channels))
            found_devices_names.append(name)
        return found_devices



if __name__ == "__main__":
    device_manager = MicrophoneManager()
    devices = device_manager.microphones
    for device_ in devices:
        print("    " + device_.name)
