from . import mvsdk
import logging
import numpy as np
from typing import Optional
from timeout_decorator import timeout, TimeoutError
from datetime import datetime
from PIL import Image
from .config import CAMERA_CONFIG_PATH
import cv2
from .config import SHAPE
import ctypes
import time
from .server_base import CameraServer
import multiprocessing as mp
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('camera')

class CameraServerLocal(CameraServer):
    TIMEOUT = 10

    def __init__(self, station_id: str, start_discard: int = 10) -> None:
        self.start_discard = start_discard
        # Check number of cameras. only supports connecting with 1 camera
        device_list = mvsdk.CameraEnumerateDevice()
        num_devices = len(device_list)
        if num_devices == 0:
            raise RuntimeError('Camera not found')
        if num_devices > 1:
            raise NotImplementedError('Multiple cameras are not currently supported')
        device_info = device_list[0]
        logger.info("\n{}: {} {}".format(device_info, device_info.GetFriendlyName(), device_info.GetPortType()))

        self.hCamera = mvsdk.CameraInit(device_info, -1, -1)
        capability = mvsdk.CameraGetCapability(self.hCamera)
        monoCamera = (capability.sIspCapacity.bMonoSensor != 0)
        mvsdk.CameraSetIspOutFormat(self.hCamera,
                                    mvsdk.CAMERA_MEDIA_TYPE_MONO8 if monoCamera else mvsdk.CAMERA_MEDIA_TYPE_BGR8)
        mvsdk.CameraReadParameterFromFile(self.hCamera, CAMERA_CONFIG_PATH)
        mvsdk.CameraPlay(self.hCamera)

        # Disable denoising by multiple exposures
        mvsdk.CameraSetDenoise3DParams(self.hCamera, 0, 4, 0)

        FrameBufferSize = (
            capability.sResolutionRange.iWidthMax * capability.sResolutionRange.iHeightMax * (1 if monoCamera else 3))
        self.pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)

        for _ in range(self.start_discard):
            try:
                self._get_image()
            except mvsdk.CameraException as e:
                logger.error(str(e.error_code) + ': ' + e.message.encode().decode('utf_8_sig'))
            except Exception as e:
                logger.error(str(type(e)) + ': ' + str(e))
        logger.info('Camera init finished')

    def __del__(self):
        mvsdk.CameraAlignFree(self.pFrameBuffer)
        mvsdk.CameraUnInit(self.hCamera)

    @timeout(TIMEOUT)
    def _get_image(self, save_buffer=None):
        # time.sleep(3)
        self.pRawData, self.FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 200)
        if save_buffer is not None:
            buffer = ctypes.addressof(save_buffer)
        else:
            buffer = self.pFrameBuffer
        mvsdk.CameraImageProcess(self.hCamera, self.pRawData, buffer, self.FrameHead)
        mvsdk.CameraReleaseImageBuffer(self.hCamera, self.pRawData)
        frame_data = (mvsdk.c_ubyte * self.FrameHead.uBytes).from_address(buffer)
        frame = np.frombuffer(frame_data, dtype=np.uint8)
        if save_buffer is not None:
            tgt_buf = np.frombuffer(save_buffer, dtype=np.uint8)
            np.copyto(tgt_buf, frame)
        frame = frame.reshape((self.FrameHead.iHeight, self.FrameHead.iWidth,
                               1 if self.FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3))
        mvsdk.CameraClearBuffer(self.hCamera)
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def get_image(self, save_buffer=None) -> Optional[np.ndarray]:
        try:
            return self._get_image(save_buffer)
        except TimeoutError:
            return None

class CameraServerLocalMP(CameraServerLocal):
    def serve_image(self, save_buffer, lock, pipe) -> None:
        lock.acquire()
        self._get_image(save_buffer)
        lock.release()
        pipe.send('init')
        while True:
            lock.acquire()
            self._get_image(save_buffer)
            lock.release()
            # if pipe.poll(10):
            pipe.recv()

def start_server_local_serve(buf, lock, pipe, *args, **kwargs):
    server = CameraServerLocalMP(*args, **kwargs)
    server.serve_image(buf, lock, pipe)

def generate_image(station_id: str, start_discard=10):
    camera = CameraServerLocal(station_id, start_discard)
    while True:
        yield camera.get_image()

def generate_image_mp(station_id: str, start_discard=10, shape=SHAPE):
    _img = np.ndarray(shape, dtype=np.uint8)
    img_arr_buf = mp.RawArray('B', _img.nbytes)
    lock = mp.Lock()
    pipe_s, pipe_c = mp.Pipe(duplex=True)
    camera_process = mp.Process(target=start_server_local_serve, args=[img_arr_buf, lock, pipe_c, station_id, start_discard], daemon=False)
    camera_process.start()
    logger.info('from client: ' + str(pipe_s.recv()))
    while True:
        pipe_s.send(1)
        lock.acquire()
        image_arr = cv2.cvtColor(np.frombuffer(img_arr_buf, dtype=np.uint8).reshape(SHAPE), cv2.COLOR_BGR2RGB)
        lock.release()
        yield image_arr

def test_get_camera_picture(vis=True, method=generate_image_mp):
    count = 0
    it = method('', 10)
    while True:
        start = datetime.now()
        frame = next(it)
        end = datetime.now()
        delta = end - start
        time.sleep(1)
        count += 1
        logger.info(f"#{count:04d} spent {delta.seconds * 1000 + delta.microseconds // 1000} ms")
        if vis:
            im = Image.fromarray(frame)
            im.save(f'/tmp/save{count}.png')
            im.show()

GEN = {
    '0': generate_image('0') # FIXME
}

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_get_camera_picture(method=generate_image_mp, vis=False)
