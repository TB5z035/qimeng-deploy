import time
from PIL import Image
import numpy as np
from timeout_decorator import timeout, TimeoutError
from typing import Optional


def get_camera_image(station_id: str, save_buffer, time_limit: int = 10) -> Optional[np.ndarray]:

    @timeout(time_limit)
    def _get_image():
        print(station_id)
        time.sleep(5)
        image_arr = np.array(Image.open('camera/test.png'), dtype=np.uint8)

    try:
        return _get_image()
    except TimeoutError:
        return None


def test_get_camera_picture():
    arr = get_camera_image(1)
    if arr is not None:
        print(arr.shape)
        Image.fromarray(arr).save('/tmp/save.png')
    else:
        print("Timeout")


if __name__ == '__main__':
    test_get_camera_picture()