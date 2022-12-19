from typing import List, Optional
import numpy as np
from camera.server_mock import get_camera_image
from apis.models import DetectionRequest
import json
import logging

logger = logging.getLogger('qimeng.ctrl.on_submit')


def handle_exception(fn):

    def with_exception_handler(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            logger.error(str(type(e)) + ': ' + str(e))
            return None

    return with_exception_handler


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

    def __str__(self) -> str:
        return str((self._shape, self._color))


@handle_exception
def on_submit(det_req: DetectionRequest):
    assert det_req.result is None
    logger.info('Started shotting')
    det_req.status = DetectionRequest.SHOTTING
    det_req.save()
    arr = get_camera_image(det_req.station_id)
    logger.info('Finished shotting')

    if det_req.search_key is not None:
        logger.info('search_key exists. Start searching')
        det_req.status = DetectionRequest.SEARCHING
        det_req.save()
        brick_list = search_list(det_req.search_key)
        logger.info('Finished searching')
    elif det_req.order_list is not None:
        logger.info('order_list exists. Start unserializing')
        order_list = json.loads(det_req.order_list)
        brick_list = [Brick(*i) for i in order_list]
        logger.info('Finished unserializing')
    else:
        brick_list = None

    logger.info('Started inferencing')
    det_req.status = DetectionRequest.RUNNING
    det_req.save()
    result = detection(arr, brick_list)
    logger.info('Finished inferencing')

    det_req.status = DetectionRequest.FINISHED
    det_req.result = json.dumps([str(i) for i in result])
    det_req.save()
    logger.info('Finished detection')


def search_list(key: str) -> List[Brick]:
    # TODO fill in implementation
    return [
        Brick(shape=key, color='Grey'),
    ]


def detection(im_arr: np.ndarray, brick_list: Optional[List[Brick]]) -> List[Brick]:
    # TODO fill in implementation
    return [
        Brick(shape='Round', color='Red'),
        Brick(shape='Square', color='Blue'),
    ]
