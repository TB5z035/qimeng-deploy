from typing import List, Optional
import numpy as np
from apis.models import DetectionRequest, Brick
import json
import time
import multiprocessing as mp
import logging
from datetime import datetime
import pickle
from PIL import Image
import zerorpc

from collections import Counter

logger = logging.getLogger('handler')

with open('/share/settings.json') as f:
    d = json.load(f)
    ALGORITHM_RPC_URL = d['algorithm_rpc_url']
    SERVER_URL = d['camera_server_url_local']


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


def parse_list(s: str) -> List[str]:
    l = json.loads(s)
    return [f"{i[0]}#{i[1]}" for i in l]


def search_list(s: str) -> List[str]:
    l = Brick.objects.filter(name__contains=s)
    return [f"{i.shape}#{i.color}" for i in l]


def on_submit(det_req: DetectionRequest):
    try:
        assert det_req.result is None

        with Timer('whole process') as timer:
            det_req.status = DetectionRequest.RUNNING
            det_req.save()
            logger.info('Started processing')

            camera_client = zerorpc.Client(SERVER_URL)
            image_arr = pickle.loads(camera_client.get_image(det_req.station_id))
            # image_arr = np.asarray(Image.open('/share/example.png'))
            # image_arr = np.asarray(Image.open('/home/tb5zhh/workspace/lego-deploy/share/example.png'))
            assert image_arr is not None
            # Image.fromarray(image_arr).save(f'/share/save-{det_req.station_id}-{datetime.now().strftime("%c")}.png')
            timer.tick('camera')

            # Search orderlist
            if det_req.order_list is not None:
                logger.info('order_list exists. Start unserializing')
                brick_list = parse_list(det_req.order_list)
            elif det_req.search_key is not None:
                logger.info('search_key exists. Start searching')
                brick_list = search_list(det_req.search_key)
                # brick_list = None
            else:
                brick_list = None
            timer.tick('search')

            # Detection
            detection_client = zerorpc.Client(ALGORITHM_RPC_URL)
            shape_results, color_results = pickle.loads(detection_client.infer(pickle.dumps(image_arr)))
            logger.info('Predictions: \n' +
                        '\n'.join([f"{shape}, {color}" for shape, color in zip(shape_results, color_results)]))

            comb_final_list = Counter([(i, j) for i, j in zip(shape_results, color_results)]).most_common(5)
            comb_final_list = [f"{i[0][0]}#{i[0][1]}" for i in comb_final_list]

            logger.info('comb_final_list: ' + str(comb_final_list))
            logger.info('brick list: ' + str(brick_list))

            if len(comb_final_list) == 0:
                det_req.result = json.dumps({"results": []})
            else:
                if brick_list is not None:
                    result = {"results": [i for i in comb_final_list if i in brick_list]}
                else:
                    result = {"results": [i for i in comb_final_list]}
                det_req.result = json.dumps(result, ensure_ascii=False)
            det_req.status = DetectionRequest.FINISHED
            det_req.save()
            timer.tick('detection')
    except Exception as e:
        logger.error(str(type(e)) + ': ' + str(e))
        det_req.status = DetectionRequest.ERROR
        det_req.save()
