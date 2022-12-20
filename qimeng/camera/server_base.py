from abc import ABCMeta, abstractmethod
from typing import Optional
import numpy as np


class CameraServer(metaclass=ABCMeta):

    @abstractmethod
    def __init__(self, station_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_image(save_buffer=None) -> Optional[np.ndarray]:
        raise NotImplementedError