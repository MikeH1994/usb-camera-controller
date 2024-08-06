import queue
import threading
import sys
import soundfile as sf
import time
from camera_manager import USBCameraDevice, CameraManager
import datetime
import os
import cv2


class CameraWriter:
    def __init__(self, device: USBCameraDevice, output_folderpath, frame_rate: float, name = None):
        self.device = device
        self.capture_stream = device.device
        self.lock = device.lock
        self.running = False
        self.output_folderpath = output_folderpath
        self.formatter = "({}) ".format(device.index) + device.name + " {}.jpg" if name is None else name + " {}.jpg"
        self.output_file = None
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
                self.timestamp_queue.put(now.strftime('%Y%m%d%H%M%S%f')[:-3])
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
            time.sleep(0.01)


if __name__ == "__main__":
    camera_manager = CameraManager()
    device = camera_manager.cameras[0]
    camera_writer = CameraWriter(device, "./", 1.0, "test camera")
    camera_writer.start()
    time.sleep(10.0)
    camera_writer.stop()
