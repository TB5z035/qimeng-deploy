from . import mvsdk
import logging
from typing import Optional
import numpy as np
import cv2
import ctypes
import pickle
from timeout_decorator import timeout
import time
import argparse
import os
import zerorpc
import sys
import random
import json
import socket

logger = logging.getLogger('Camera Client')
with open('/share/settings.json') as f:
    d = json.load(f)
    SERVER_URL = d['camera_server_url']
    CAMERA_CONFIG_PATH = d['camera_config']

class CameraClient:
    TIMEOUT = 10

    @staticmethod
    def online_camera_sns():
        device_list = mvsdk.CameraEnumerateDevice()
        sn_list = [device.acSn.decode() for device in device_list]
        logger.info('Available devices: \n' + str('\n'.join(sn_list)))
        return sn_list

    def __init__(self, station_id: str, camera_sn: str, start_discard: int = 10, denoising=True) -> None:
        self.station_id = station_id
        self.start_discard = start_discard
        self.camera_sn = camera_sn

        # Check number of cameras
        device_list = mvsdk.CameraEnumerateDevice()
        sn_list = [device.acSn.decode() for device in device_list]
        logger.info('Available devices: \n' + str('\n'.join(sn_list)))
        devices = [i for i in device_list if i.acSn.decode() == camera_sn]
        assert len(devices) == 1, f'{len(devices)} camera exist with SN {camera_sn}'
        device_info = devices[0]

        logger.info("\n{}: {} {}".format(device_info, device_info.GetFriendlyName(), device_info.GetPortType()))

        self.hCamera = mvsdk.CameraInit(device_info, -1, -1)
        capability = mvsdk.CameraGetCapability(self.hCamera)
        monoCamera = (capability.sIspCapacity.bMonoSensor != 0)
        mvsdk.CameraSetIspOutFormat(self.hCamera,
                                    mvsdk.CAMERA_MEDIA_TYPE_MONO8 if monoCamera else mvsdk.CAMERA_MEDIA_TYPE_BGR8)
        mvsdk.CameraReadParameterFromFile(self.hCamera, CAMERA_CONFIG_PATH)
        mvsdk.CameraPlay(self.hCamera)

        # Disable denoising by multiple exposures
        self.denoising = denoising
        if denoising:
            mvsdk.CameraSetDenoise3DParams(self.hCamera, 1, 4, (0.25, 0.25, 0.25, 0.25))
        else:
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

        def shot(self):
            self.pRawData, self.FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 200)
            mvsdk.CameraImageProcess(self.hCamera, self.pRawData, buffer, self.FrameHead)
            mvsdk.CameraReleaseImageBuffer(self.hCamera, self.pRawData)

        if save_buffer is not None:
            buffer = ctypes.addressof(save_buffer)
        else:
            buffer = self.pFrameBuffer

        for _ in range(4 if self.denoising else 1):
            shot(self)
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


class CameraClientMP(CameraClient):

    def serve_image(self, save_buffer, lock, pipe) -> None:
        lock.acquire()
        self._get_image(save_buffer)
        lock.release()
        pipe.send('init')
        while True:
            lock.acquire()
            self._get_image(save_buffer)
            lock.release()
            time.sleep(0.1)


class CameraClientRPC(CameraClient):

    def __init__(self,
                 station_id: str,
                 camera_sn: str,
                 start_discard: int = 10,
                 station_url=None,
                 server_port=None) -> None:
        super().__init__(station_id, camera_sn, start_discard)
        assert station_url is not None
        assert server_port is not None
        client = zerorpc.Client(SERVER_URL)
        client.register_rpc(station_id, station_url)
        client.close()
        self.station_url = station_url
        self.server_port = server_port

    def serve(self):
        server = zerorpc.Server(self)
        server.bind(f"tcp://0.0.0.0:{self.server_port}")
        logger.info(f'Camera client serving at {self.station_url}')
        try:
            server.run()
        except Exception as e:
            logger.error(str(type(e)) + ': ' + str(e))
        finally:
            server.close()

    def get_image(self, save_buffer=None) -> Optional[bytes]:
        return pickle.dumps(super()._get_image(save_buffer))

    def __del__(self):
        client = zerorpc.Client(SERVER_URL)
        client.unregister_rpc(self.station_id)
        client.close()
        return super().__del__()


def camera_client_serve(buf, lock, pipe, *args, **kwargs):
    server = CameraClientMP(*args, **kwargs)
    server.serve_image(buf, lock, pipe)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('--station_id', type=str, default=socket.gethostname())
    parser.add_argument('--port', type=int, default=8383)
    args = parser.parse_args()

    sn = CameraClient.online_camera_sns()
    assert len(sn) == 1, "RPC camera client supports only 1 camera"
    local_sn = sn[0]
    camera = CameraClientRPC(
        args.station_id, local_sn, server_port=args.port, station_url=f'tcp://{args.station_id}:{args.port}')
    camera.serve()