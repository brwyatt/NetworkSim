import logging

from networksim.stack import Stack


logger = logging.getLogger(__name__)


class IPStack(Stack):
    def __init__(self):
        super().__init__()
