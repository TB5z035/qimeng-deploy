from . import mvsdk
import logging
import numpy as np
from typing import Optional
from timeout_decorator import timeout, TimeoutError
import time
from PIL import Image
import platform

from .config import CAMERA_CONFIG_PATH, SHAPE

logger = logging.getLogger('camera')
def get_camera_image(station_id: str, save_buffer=None, time_limit: int = 10) -> Optional[np.ndarray]:

    @timeout(time_limit)
    def _get_image():
        time.sleep(1)
        share_arr = np.ndarray(SHAPE, buffer=save_buffer, dtype=np.uint8)
        image_arr = np.asarray(Image.open('camera/test.png'), dtype=np.uint8)
        np.copyto(share_arr, image_arr)

    try:
        return _get_image()
    except TimeoutError:
        return None

def get_camera_image(station_id: str, save_buffer=None, time_limit: int = 10) -> Optional[np.ndarray]:
    global hCamera, FrameBufferSize
    logger.info('Start taking images')

    # Check number of cameras. only supports connecting with 1 camera
    device_list = mvsdk.CameraEnumerateDevice()
    num_devices = len(device_list)
    if num_devices == 0:
        raise RuntimeError('Camera not found')
    if num_devices > 1:
        raise NotImplementedError('Multiple cameras are not currently supported')
    device_info = device_list[0]
    logger.info("{}: {} {}".format(device_info, device_info.GetFriendlyName(), device_info.GetPortType()))
    logger.info(device_info)

    try:
        hCamera = mvsdk.CameraInit(device_info, -1, -1)
    except mvsdk.CameraException as e:
        logger.info("CameraInit Failed({}): {}".format(e.error_code, e.message))
        raise

    capability = mvsdk.CameraGetCapability(hCamera)
    monoCamera = (capability.sIspCapacity.bMonoSensor != 0)
    mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8 if monoCamera else mvsdk.CAMERA_MEDIA_TYPE_BGR8)
    mvsdk.CameraReadParameterFromFile(hCamera, CAMERA_CONFIG_PATH)
    mvsdk.CameraPlay(hCamera)


    FrameBufferSize = capability.sResolutionRange.iWidthMax * capability.sResolutionRange.iHeightMax * (1 if monoCamera else 3)

    pFrameBuffer_ = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)
    mvsdk.CameraSetDenoise3DParams(hCamera, 0, 4, 0)

    # Capture
    pRawData, FrameHead = mvsdk.CameraGetImageBuffer(hCamera, 2000)
    mvsdk.CameraImageProcess(hCamera, pRawData, pFrameBuffer_, FrameHead)
    mvsdk.CameraReleaseImageBuffer(hCamera, pRawData)
    if platform.system() == "Windows":
        mvsdk.CameraFlipFrameBuffer(pFrameBuffer_, FrameHead, 1)
    frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(pFrameBuffer_)
    frame = np.frombuffer(frame_data, dtype=np.uint8)
    frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 1 if monoCamera else 3))
    # q_img.put(frame)

    mvsdk.CameraUnInit(hCamera)
    mvsdk.CameraAlignFree(pFrameBuffer_)
