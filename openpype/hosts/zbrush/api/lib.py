#zscript command etc.
import os
import logging
import tempfile
from . import CommunicationWrapper


log = logging.getLogger("zbrush.lib")


def execute_zscript(zscript, communicator=None):
    if not communicator:
        communicator = CommunicationWrapper.communicator
    return communicator.execute_zscript(zscript)
