import logging
import numpy as np
from typing import Optional
from datetime import datetime
from PIL import Image
from .config import *
from .client import CameraClient, camera_client_serve
import cv2
import pickle
import time
import multiprocessing as mp
import zerorpc
logger = logging.getLogger('camera')

class ImageServer:
    URL = f"tcp://0.0.0.0:{SERVER_PORT}"

    def __init__(self) -> None:
        self.stations = {}
        self.stations_type = {}
        self.locks = {}
        self.img_arr_buf = {}
        self.pipes = {}
        for station_id, dev in CLIENT_MP_SNS.items():
            self.register_mp(station_id, dev)


    def register_mp(self, station_id, device_sn, shape=SHAPE):
        _img = np.ndarray(shape, dtype=np.uint8)
        self.img_arr_buf[station_id] = mp.RawArray('B', _img.nbytes)
        self.locks[station_id] = mp.Lock()
        self.pipes[station_id], pipe_c = mp.Pipe(duplex=True)
        self.stations[station_id] = mp.Process(
            target=camera_client_serve,
            args=[
                self.img_arr_buf[station_id],
                self.locks[station_id],
                pipe_c,
                station_id,
                device_sn,
            ],
            daemon=False)
        self.stations[station_id].start()
        self.stations_type[station_id] = 'mp'
        logger.info('from client: ' + str(self.pipes[station_id].recv()))

    def register_rpc(self, station_id, station_url) -> bool:
        if station_id in self.stations:
            logger.error(f"Station ID {station_id} exists. Registration failed")
            return False
        self.stations[station_id] = zerorpc.Client(station_url)
        self.stations_type[station_id] = 'rpc'
        logger.info(f"Station registered with ID {station_id} at {station_url}")
        return True
    
    def unregister_rpc(self, station_id: str) -> bool:
        if station_id not in self.stations or self.stations_type[station_id] != 'rpc':
            logger.error(f"Illegal unregistration")
            return False
        else:
            logger.info(f"Station unregistered with ID {station_id}")
            del self.stations[station_id]
            del self.stations_type[station_id]
            return True

    def get_image(self, station_id: str) -> Optional[bytes]:
        if station_id not in self.stations:
            logger.error(f"Station ID {station_id} doesn't exist. Get image failed")
            return None
        logger.info(f'Get image from {station_id} ({self.stations_type[station_id]})')
        if self.stations_type[station_id] == 'rpc':
            return self.stations[station_id].get_image()
        elif self.stations_type[station_id] == 'mp':
            self.pipes[station_id].send(1)
            self.locks[station_id].acquire()
            image_arr = cv2.cvtColor(
                np.frombuffer(self.img_arr_buf[station_id], dtype=np.uint8).reshape(SHAPE), cv2.COLOR_BGR2RGB)
            self.locks[station_id].release()
            return pickle.dumps(image_arr)
        else:
            raise NotImplementedError

    def yield_image(self, station_id: str):
        while True:
            ret = self.get_image(station_id)
            if ret is None:
                yield None
            else:
                yield pickle.loads(ret)

    def serve(self):
        server = zerorpc.Server(self)
        server.bind(self.URL)
        server.run()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    server = ImageServer()
    server.serve()