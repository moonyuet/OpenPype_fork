"""Pipeline tools for OpenPype Zbrush integration."""
import os
import logging
from operator import attrgetter

import json


from openpype.host import HostBase, IWorkfileHost, ILoadHost, IPublishHost
import pyblish.api
from openpype.pipeline import (
    register_creator_plugin_path,
    register_loader_plugin_path,
    AVALON_CONTAINER_ID,
)
from openpype.hosts.zbrush import ZBRUSH_HOST_DIR


PLUGINS_DIR = os.path.join(ZBRUSH_HOST_DIR, "plugins")
PUBLISH_PATH = os.path.join(PLUGINS_DIR, "publish")
LOAD_PATH = os.path.join(PLUGINS_DIR, "load")
CREATE_PATH = os.path.join(PLUGINS_DIR, "create")
INVENTORY_PATH = os.path.join(PLUGINS_DIR, "inventory")

log = logging.getLogger("openpype.hosts.zbrush")

class ZbrushHost(HostBase, IWorkfileHost, ILoadHost, IPublishHost):
    name = "zbrush"
    menu = None

    def __init__(self):
        super(ZbrushHost, self).__init__()
        self._op_events = {}
        self._has_been_setup = False

    def install(self):
        pyblish.api.register_host("zbrush")

        pyblish.api.register_plugin_path(PUBLISH_PATH)
        register_loader_plugin_path(LOAD_PATH)
        register_creator_plugin_path(CREATE_PATH)
        log.info("Installing menu ... ")
        self._install_menu()


        self._has_been_setup = True

    def _install_menu(self):
        cmds = []
        for file in ["ayon_zbrush_menu.txt", "ayon_zbrush_menu.zsc"]:
            zbrush_path = os.environ["ZBRUSH_PLUGIN_PATH"]
            origFile = os.path.join(ZBRUSH_HOST_DIR, file)
            targetFile = os.path.join(zbrush_path[-1], file)
            _, ext = os.path.splitext(file)
            if ext == ".txt":
                with open(origFile, "r") as init:
                    initStr = init.read()
                env = os.environ["AYON_ROOT"] or os.environ["OPENPYPE_ROOT"]
                initStr = initStr.replace("AYONROOT", "%s" % env)
                python_exe = os.path.join(os.environ["PYTHONPATH"][0],
                                          "python.exe").replace("\\", "/")
                initStr = initStr.replace("PYTHONEXE",python_exe)
                initStr = initStr.replace("AYONZBRUSHHOST", "%s" % ZBRUSH_HOST_DIR)
            with open(targetFile, "w") as target:
                target.write(initStr)
                target.close()

    def save_file(self, dst_path=None):
        return super().save_file(dst_path)
    def open_file(self, filepath):
        return super().open_file(filepath)
