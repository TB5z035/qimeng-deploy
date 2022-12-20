from typing import List, Optional
import numpy as np
from camera.server_local import generate_image_mp
from camera.config import SHAPE
from apis.models import DetectionRequest
import json
import time
import multiprocessing as mp
import logging
from datetime import datetime

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

def on_submit(det_req: DetectionRequest, sess):
    now = datetime.now()
    try:
        assert det_req.result is None

        logger.info('Started shotting')
        det_req.status = DetectionRequest.RUNNING
        det_req.save()
        
        if det_req.station_id not in sess:
            sess[det_req.station_id] = generate_image_mp(det_req.station_id)
        image_arr = next(sess[det_req.station_id])

        # Search orderlist
        if det_req.order_list is not None:
            logger.info('order_list exists. Start unserializing')
            brick_list = parse_list(det_req.order_list)
        elif det_req.search_key is not None:
            logger.info('search_key exists. Start searching')
            brick_list = search_list(det_req.search_key)
        else:
            brick_list = None

        # Detection
        result = detection(image_arr, brick_list)
        logger.info('Finished inferencing')

        det_req.status = DetectionRequest.FINISHED
        det_req.result = json.dumps([i.as_tuple() for i in result])
        det_req.save()
        logger.info('Finished detection')
    except Exception as e:
        logger.error(str(type(e)) + ': ' + str(e))

    new_now = datetime.now()
    logger.info(f"Spent {(new_now - now).seconds * 1000 + (new_now - now).microseconds // 1000 } ms")


def parse_list(buffer: str) -> List[Brick]:
    order_list = json.loads(buffer)
    return [Brick(*i) for i in order_list]


def search_list(key: str) -> List[Brick]:
    # TODO fill in implementation
    time.sleep(1)
    return [
        Brick(shape=key, color='Grey'),
    ]


def detection(im_arr: np.ndarray, brick_list: Optional[List[Brick]]) -> List[Brick]:
    time.sleep(1)
    # TODO fill in implementation
    return [
        Brick(shape='Round', color='Red'),
        Brick(shape='Square', color='Blue'),
    ]
