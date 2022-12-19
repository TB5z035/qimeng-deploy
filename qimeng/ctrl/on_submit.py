from typing import List, Optional
import numpy as np
from camera.server_mock import get_camera_image
from apis.models import DetectionRequest
import json
import asyncio
import time
import threading
import multiprocessing as mp
import logging

logger = logging.getLogger('qimeng.ctrl.on_submit')


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


def on_submit(det_req: DetectionRequest):
    try:
        assert det_req.result is None

        logger.info('Started shotting')
        det_req.status = DetectionRequest.RUNNING
        det_req.save()

        # camera_task = asyncio.create_task(get_camera_image(det_req.station_id))
        # camera_thread = threading.Thread(target=get_camera_image, args=[det_req.station_id])
        shared_buffer = mp.RawArray('B', 4224 * 3672 * 3)
        camera_process = mp.Process(target=get_camera_image, args=[det_req.station_id, shared_buffer])
        camera_process.start()

        if det_req.search_key is not None:
            logger.info('search_key exists. Start searching')
            brick_list_task = asyncio.create_task(search_list(det_req.search_key))
        elif det_req.order_list is not None:
            logger.info('order_list exists. Start unserializing')
            brick_list_task = asyncio.create_task(parse_list(det_req.order_list))
        else:
            brick_list_task = None

        camera_thread.join()
        # arr = camera_task
        if brick_list_task is not None:
            brick_list = brick_list_task
        else:
            brick_list = None

        result = detection(arr, brick_list)
        logger.info('Finished inferencing')

        det_req.status = DetectionRequest.FINISHED
        det_req.result = json.dumps([i.as_tuple() for i in result])
        det_req.save()
        logger.info('Finished detection')
    except Exception as e:
        logger.error(str(type(e)) + ': ' + str(e))


def parse_list(buffer: str) -> List[Brick]:
    order_list = json.loads(buffer)
    return [Brick(*i) for i in order_list]


def search_list(key: str) -> List[Brick]:
    # TODO fill in implementation
    time.sleep(5)
    return [
        Brick(shape=key, color='Grey'),
    ]


def detection(im_arr: np.ndarray, brick_list: Optional[List[Brick]]) -> List[Brick]:
    # TODO fill in implementation
    return [
        Brick(shape='Round', color='Red'),
        Brick(shape='Square', color='Blue'),
    ]
