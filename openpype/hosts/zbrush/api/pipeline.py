"""Pipeline tools for OpenPype Zbrush integration."""
import os
import logging
from operator import attrgetter

import json

SECTION_NAME_CONTEXT = "context"
from openpype.host import HostBase, IWorkfileHost, ILoadHost, IPublishHost
import pyblish.api
from openpype.pipeline import (
    legacy_io,
    register_creator_plugin_path,
    register_loader_plugin_path,
    AVALON_CONTAINER_ID,
)
from openpype.lib import register_event_callback
from openpype.hosts.zbrush import ZBRUSH_HOST_DIR


PLUGINS_DIR = os.path.join(ZBRUSH_HOST_DIR, "plugins")
PUBLISH_PATH = os.path.join(PLUGINS_DIR, "publish")
LOAD_PATH = os.path.join(PLUGINS_DIR, "load")
CREATE_PATH = os.path.join(PLUGINS_DIR, "create")
INVENTORY_PATH = os.path.join(PLUGINS_DIR, "inventory")

log = logging.getLogger("openpype.hosts.zbrush")

class ZbrushHost(HostBase, IWorkfileHost, ILoadHost, IPublishHost):
    name = "zbrush"

    def install(self):
        legacy_io.install()

        # Create workdir folder if does not exist yet
        workdir = legacy_io.Session["AVALON_WORKDIR"]
        if not os.path.exists(workdir):
            os.makedirs(workdir)

        plugins_dir = os.path.join(ZBRUSH_HOST_DIR, "plugins")
        publish_dir = os.path.join(plugins_dir, "publish")
        load_dir = os.path.join(plugins_dir, "load")
        create_dir = os.path.join(plugins_dir, "create")

        pyblish.api.register_host("zbrush")
        pyblish.api.register_plugin_path(publish_dir)
        register_loader_plugin_path(load_dir)
        register_creator_plugin_path(create_dir)

    def get_current_project_name(self):
        """
        Returns:
            Union[str, None]: Current project name.
        """

        return self.get_current_context().get("project_name")

    def get_current_asset_name(self):
        """
        Returns:
            Union[str, None]: Current asset name.
        """

        return self.get_current_context().get("asset_name")

    def get_current_task_name(self):
        """
        Returns:
            Union[str, None]: Current task name.
        """

        return self.get_current_context().get("task_name")

    # --- Workfile ---
    def open_workfile(self, filepath):

        return True

    def save_workfile(self, filepath=None):
        return True

    def work_root(self, session):
        return session["AVALON_WORKDIR"]

    def get_current_workfile(self):
        return True

    def workfile_has_unsaved_changes(self):
        return None

    def get_workfile_extensions(self):
        return [".zpr"]

    def save_workfile(self, dst_path=None):
        return dst_path

    def open_workfile(self, filepath):
        return filepath

    def get_current_workfile(self):
        return ""

    def save_file(self, dst_path=None):
        return super().save_file(dst_path)

    def list_instances(self):
        return ls()


def ls() -> list:
    """Get all OpenPype instances."""
    return []


def containerise(name: str, nodes: list, context,
                 namespace=None, loader=None, suffix="_CON"):
    data = {
        "schema": "openpype:container-2.0",
        "id": AVALON_CONTAINER_ID,
        "name": name,
        "namespace": namespace or "",
        "loader": loader,
        "representation": context["representation"]["_id"],
    }

    return data
