from typing import List, Optional
import numpy as np
from apis.models import DetectionRequest
import json
import time
import multiprocessing as mp
import logging
from datetime import datetime
import pickle
from PIL import Image
import zerorpc

from .config import *

from camera.config import *

logger = logging.getLogger('handler')


class Brick:

    def __init__(self, **kwargs) -> None:
        self._shape = kwargs['shape']
        self._color = kwargs['color']

    @property
    def color(self, color_id: str):
        self._color = color_id

    @property
    def shape(self, shape_id: str):
        self._shape = shape_id

    def as_tuple(self):
        return (self._shape, self._color)

    def __str__(self) -> str:
        return str((self._shape, self._color))


class Timer(object):

    def __init__(self, name):
        self.names = []
        self.logger = logging.getLogger(f'timer({name})')

    def tick(self, name):
        self.steps.append(datetime.now())
        self.names.append(name)

    def __enter__(self):
        self.steps = [datetime.now()]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for i in range(len(self.names)):
            delta = self.steps[i + 1] - self.steps[i]
            self.logger.info(f"{self.names[i]:10} spent {delta.seconds * 1000 + delta.microseconds // 1000} ms")


def on_submit(det_req: DetectionRequest):
    now = datetime.now()
    try:
        assert det_req.result is None

        with Timer('whole process') as timer:
            det_req.status = DetectionRequest.RUNNING
            det_req.save()
            logger.info('Started processing')

            camera_client = zerorpc.Client(SERVER_URL)
            image_arr = pickle.loads(camera_client.get_image(det_req.station_id))
            assert image_arr is not None
            Image.fromarray(image_arr).save(f'/share/save-{det_req.station_id}.png')
            logger.warning(image_arr.dtype)
            timer.tick('camera')

            # Search orderlist
            if det_req.order_list is not None:
                logger.info('order_list exists. Start unserializing')
                brick_list = parse_list(det_req.order_list)
            elif det_req.search_key is not None:
                logger.info('search_key exists. Start searching')
                brick_list = search_list(det_req.search_key)
            else:
                brick_list = None
            timer.tick('search')

            # Detection
            detection_client = zerorpc.Client(ALGORITHM_RPC_URL)
            Image.fromarray(image_arr).save(f'/share/save2-{det_req.station_id}.png')
            Image.fromarray(pickle.loads(pickle.dumps(image_arr))).save(f'/share/save3-{det_req.station_id}.png')
            result = pickle.loads(detection_client.infer(pickle.dumps(image_arr)))
            logger.info(result)
            result = {str(i): str((result[i][0][:, 5] > 0.2).sum()) for i in range(len(result))}  # include class map
            timer.tick('detection')

            det_req.status = DetectionRequest.FINISHED
            det_req.result = json.dumps(result)
            det_req.save()
    except Exception as e:
        logger.error(str(type(e)) + ': ' + str(e))

    new_now = datetime.now()
    logger.info(f"Spent {(new_now - now).seconds * 1000 + (new_now - now).microseconds // 1000 } ms")


def parse_list(buffer: str) -> List[Brick]:
    order_list = json.loads(buffer)
    return [Brick(*i) for i in order_list]


def search_list(key: str) -> List[Brick]:
    # TODO fill in implementation
    # time.sleep(1)
    return [
        Brick(shape=key, color='Grey'),
    ]


def detection(im_arr: np.ndarray, brick_list: Optional[List[Brick]]) -> List[Brick]:
    # time.sleep(1)
    # TODO fill in implementation
    return [
        Brick(shape='Round', color='Red'),
        Brick(shape='Square', color='Blue'),
    ]
