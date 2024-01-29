import os
import logging
import tempfile
import subprocess
import tempfile
import traceback
import socket
from contextlib import closing
from multiprocessing.connection import Client
from openpype.hosts.zbrush.api.lib import execute_zscript


KEY = bytes('secret', 'utf-8')
ADDRESS = 'localhost'
log = logging.getLogger("check_connection")


# Take reference from this script
# https://github.com/JonasOuellet/zlayermanager/blob/master/src/zlm_sender/communicate.py
class ClientConnection(object):
    def __init__(self):
        self._conn = None
        self.port = self.find_free_port()

    def __enter__(self):
        if self.connect():
            return self._conn
        else:
            return None

    def __exit__(self, type, value, traceback):
        self.close()

    @staticmethod
    def find_free_port():
        with closing(
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ) as sock:
            sock.bind(("", 0))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            port = sock.getsockname()[1]
        return port

    def connect(self):
        try:
            port = self.port
            if port is not None:
                address = (ADDRESS, port)
                self._conn = Client(address, authkey=KEY)
                return True
        except Exception as e:
            print(e)

        return False

    def close(self):
        if self._conn:
            self._conn.close()

        self._conn = None

    def send(self, *args):
        try:
            self._conn.send(args)
        except Exception:
            pass


def safe_excepthook(*args):
    traceback.print_exception(*args)


def open_widgets(launcher_type=None):
    conn = ClientConnection()
    # error when connecting so it means that the UI is not opened
    if not conn.connect():
        from openpype.hosts.zbrush.api import widgets
        if launcher_type == "Creator":
            return widgets.LaunchCreator()
        elif launcher_type == "Publisher":
            return widgets.LaunchPublisher()
        elif launcher_type == "Loader":
            return widgets.LaunchLoader()
        elif launcher_type == "Sceneinventory":
            return widgets.LaunchSceneInventory()
        elif launcher_type == "Workfile":
            return widgets.LaunchWorkFiles()
    if launcher_type:
        conn.send(f"{launcher_type} update", launcher_type)

    conn.close()


def update_from_zbrush():
    conn = ClientConnection()
    # error when connecting so it means that the UI is not opened
    if conn.connect():
        conn.send('update_from_zbrush')
    conn.close()


def update_zbrush():
    conn = ClientConnection()
    # error when connecting so it means that the UI is not opened
    if conn.connect():
        conn.send('update_zbrush')
    conn.close()


def send_execute_zscript(zscript):
    conn = ClientConnection()

    if conn.connect():
        execute_zscript(zscript)
        conn.send("execute_zscript", zscript)

    conn.close()
