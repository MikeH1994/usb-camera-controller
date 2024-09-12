import queue
import threading
import time

import utils
from camera_manager import USBCameraDevice, CameraManager
import datetime
import os
import cv2


class CameraWriter:
    def __init__(self, device: USBCameraDevice, output_root, frame_rate: float, name = None):
        self.device = device
        self.capture_stream = device.device
        self.lock = device.lock
        self.running = False
        self.output_root = output_root
        self.output_folderpath = os.path.join(output_root, name) if name is not None else os.path.join(output_root, device.name)
        if not os.path.exists(self.output_folderpath):
            os.mkdir(self.output_folderpath)
        self.formatter = "({}) ".format(device.index) + device.name + " {}.jpg" if name is None else name + " {}.jpg"
        self.formatter_avi = self.formatter.replace(".jpg", ".avi")
        self.output_avi_file = None
        self.image_queue = queue.Queue()
        self.timestamp_queue = queue.Queue()
        self.write_thread = threading.Thread(target=self.write_loop)
        self.capture_thread = threading.Thread(target=self.capture_loop)
        self.frame_rate = frame_rate

    def start(self):
        self.running = True
        self.write_thread.start()
        self.capture_thread.start()

    def stop(self):
        self.running = False
        self.write_thread.join()
        self.capture_thread.join()

    def capture_loop(self):
        assert(self.frame_rate > 0.0)
        time_between_frames = 1.0 / self.frame_rate
        while self.running:
            now = datetime.datetime.now()
            t1 = time.time()
            self.lock.acquire()
            ret, frame = self.capture_stream.read()
            self.lock.release()
            if ret:
                self.image_queue.put(frame)
                self.timestamp_queue.put(now.strftime(utils.get_timestamp_format())[:-3])
            t2 = time.time()

            time_taken = t2 - t1
            if time_taken < time_between_frames:
                time.sleep(time_between_frames - time_taken)

    def write_loop(self):
        while self.running or not self.image_queue.empty():
            if not self.image_queue.empty():
                image = self.image_queue.get()
                timestamp = self.timestamp_queue.get()
                filepath = os.path.join(self.output_folderpath, self.formatter.format(timestamp))
                cv2.imwrite(filepath, image)

                if self.output_avi_file is None:
                    timestamp_str = datetime.datetime.now().strftime(utils.get_timestamp_format())[:-3]
                    avi_filename = os.path.join(self.output_root, self.formatter_avi.format(timestamp_str))
                    output_size = (image.shape[1], image.shape[0])

                    codec = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
                    self.output_avi_file = cv2.VideoWriter(avi_filename, codec, self.frame_rate, output_size)
                self.output_avi_file.write(image)
            time.sleep(0.01)

        if self.output_avi_file is not None:
            self.output_avi_file.release()