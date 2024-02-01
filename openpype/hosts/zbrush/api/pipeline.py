"""Pipeline tools for OpenPype Zbrush integration."""
import os
import logging
import requests

import pyblish.api

from openpype.host import HostBase, IWorkfileHost, ILoadHost, IPublishHost
from openpype.pipeline import (
    legacy_io,
    register_creator_plugin_path,
    register_loader_plugin_path,
    AVALON_CONTAINER_ID,
)
from openpype.pipeline.context_tools import get_global_context
from openpype.settings import get_current_project_settings
from openpype.lib import register_event_callback
from openpype.hosts.zbrush import ZBRUSH_HOST_DIR
from .workio import (
    save_file, open_file,
    get_current_filepath
)

SECTION_NAME_CONTEXT = "context"
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

        register_event_callback("application.exit", self.application_exit)


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

    def get_current_context(self):
        context = get_current_workfile_context()
        if not context:
            return get_global_context()

        if "project_name" in context:
            return context
        # This is legacy way how context was stored
        return {
            "project_name": context.get("project"),
            "asset_name": context.get("asset"),
            "task_name": context.get("task")
        }
    # --- Workfile ---
    def open_workfile(self, filepath):
        open_file(filepath)
        return filepath

    def save_workfile(self, filepath=None):
        if not filepath:
            filepath = self.get_current_workfile()
        save_file(filepath)
        return filepath

    def work_root(self, session):
        return session["AVALON_WORKDIR"]

    def get_current_workfile(self):
        return get_current_filepath()

    def workfile_has_unsaved_changes(self):
        # from time import gmtime, strftime
        # current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        # print(current_time)

        return None

    def get_workfile_extensions(self):
        return [".zpr"]

    def list_instances(self):
        return ls()


    def application_exit(self):
        """Logic related to TimerManager.

        Todo:
            This should be handled out of TVPaint integration logic.
        """

        data = get_current_project_settings()
        stop_timer = data["tvpaint"]["stop_timer_on_application_exit"]

        if not stop_timer:
            return

        # Stop application timer.
        webserver_url = os.environ.get("OPENPYPE_WEBSERVER_URL")
        rest_api_url = "{}/timers_manager/stop_timer".format(webserver_url)
        requests.post(rest_api_url)


def ls() -> list:
    """Get all OpenPype instances."""
    return []


def get_current_workfile_context():
    pass

def get_workfile_metadata(metadata_key, default=None):
    pass

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
