import queue
import threading
import sys
import soundfile as sf
import time
import os
import datetime
import sounddevice as sd
from microphone_manager import MicrophoneDevice
import utils


class MicrophoneWriter:
    def __init__(self, device: MicrophoneDevice, output_root, name=None):
        self.device = device
        self.stream = sd.InputStream(channels=device.channels, blocksize=int(device.samplerate), callback=self.callback)
        self.running = False
        self.output_root = output_root
        self.output_folderpath = os.path.join(output_root, name) if name is not None else os.path.join(output_root, device.name)

        if not os.path.exists(self.output_folderpath):
            os.mkdir(self.output_folderpath)

        self.formatter = "({}) ".format(device.index) + device.name + " {}.wav" if name is None else name + " {}.wav"
        self.sample_rate = device.samplerate
        self.n_channels = device.channels
        self.output_file = None
        self.data_queue = queue.Queue()
        self.write_thread = threading.Thread(target=self.write_loop)

    def callback(self, indata, _, __, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.data_queue.put(indata.copy())

    def start(self):
        self.running = True
        self.stream.callback = self.callback
        timestamp_str = datetime.datetime.now().strftime(utils.get_timestamp_format())[:-3]
        output_filepath = os.path.join(self.output_folderpath, self.formatter.format(timestamp_str))
        self.output_file = sf.SoundFile(output_filepath, mode='w', samplerate=int(self.sample_rate),
                                        channels=self.n_channels)
        self.write_thread.start()
        self.stream.start()

    def stop(self):
        self.running = False
        self.stream.stop()
        self.write_thread.join()

    def write_loop(self):
        while self.running or not self.data_queue.empty():
            if not self.data_queue.empty():
                self.output_file.write(self.data_queue.get())
            time.sleep(0.01)
