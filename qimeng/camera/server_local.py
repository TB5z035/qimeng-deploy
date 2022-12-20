from . import mvsdk
import logging
import numpy as np
from typing import Optional
from timeout_decorator import timeout, TimeoutError
import time
from PIL import Image
import platform
from datetime import datetime
from .config import CAMERA_CONFIG_PATH, SHAPE
import cv2
from timeout_decorator import timeout, TimeoutError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('camera')


def get_camera_image(station_id: str, save_buffer=None, time_limit: int = 1) -> Optional[np.ndarray]:
    logger.info('Start taking images')

    # Check number of cameras. only supports connecting with 1 camera
    device_list = mvsdk.CameraEnumerateDevice()
    num_devices = len(device_list)
    if num_devices == 0:
        raise RuntimeError('Camera not found')
    if num_devices > 1:
        raise NotImplementedError('Multiple cameras are not currently supported')
    device_info = device_list[0]
    logger.info("\n{}: {} {}".format(device_info, device_info.GetFriendlyName(), device_info.GetPortType()))

    hCamera = mvsdk.CameraInit(device_info, -1, -1)
    capability = mvsdk.CameraGetCapability(hCamera)
    monoCamera = (capability.sIspCapacity.bMonoSensor != 0)
    mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8 if monoCamera else mvsdk.CAMERA_MEDIA_TYPE_BGR8)
    mvsdk.CameraReadParameterFromFile(hCamera, CAMERA_CONFIG_PATH)
    mvsdk.CameraPlay(hCamera)
    FrameBufferSize = (
        capability.sResolutionRange.iWidthMax * capability.sResolutionRange.iHeightMax * (1 if monoCamera else 3))

    mvsdk.CameraSetDenoise3DParams(hCamera, 0, 4, 0)
    pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)
    try:
        count = 0
        while True:
            try:

                @timeout(time_limit)
                def _get_image():
                    # time.sleep(3)
                    pRawData, FrameHead = mvsdk.CameraGetImageBuffer(hCamera, 200)
                    mvsdk.CameraImageProcess(hCamera, pRawData, pFrameBuffer, FrameHead)
                    frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(pFrameBuffer)
                    frame = np.frombuffer(frame_data, dtype=np.uint8)
                    frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth,
                                           1 if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3))
                    mvsdk.CameraReleaseImageBuffer(hCamera, pRawData)
                    return frame

                frame = _get_image()
                if count < 10:
                    count += 1
                    continue
                yield cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            except mvsdk.CameraException as e:
                logger.error(str(e.error_code) + ': ' + e.message)
            except KeyboardInterrupt:
                raise
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logger.error(str(type(e)) + ': ' + str(e))
    finally:
        mvsdk.CameraAlignFree(pFrameBuffer)
        mvsdk.CameraUnInit(hCamera)
        yield None


def test_get_camera_picture():
    gen = get_camera_image(10)
    count = 0
    while True:
        start = datetime.now()
        arr = next(gen)
        end = datetime.now()
        logger.debug(f'Spent {(end - start).seconds * 1000 + (end - start).microseconds // 1000 } ms')
        if arr is not None:

            im = Image.fromarray(arr)
            im.save(f'/tmp/save{count}.png')
            count += 1


if __name__ == '__main__':
    test_get_camera_picture()
