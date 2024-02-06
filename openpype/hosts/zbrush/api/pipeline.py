"""Pipeline tools for OpenPype Zbrush integration."""
import os
import ast
import logging
import requests
import tempfile
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
from .lib import execute_zscript

METADATA_SECTION = "avalon"
ZBRUSH_SECTION_NAME_CONTEXT = "context"
ZBRUSH_METADATA_CREATE_CONTEXT = "create_context"
ZBRUSH_SECTION_NAME_INSTANCES = "instances"
ZBRUSH_SECTION_NAME_CONTAINERS = "containers"

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
        open_file_zscript = ("""
[IFreeze,
[MemCreate, currentfile, 100, 0]
[VarSet, filename, "{filepath}"]
[MemWriteString, currentfile, #filename, 0]
[FileNameSetNext, #filename]
[IKeyPress, 13, [IPress, File:Open:Open]]]
]
    """).format(filepath=filepath)
        execute_zscript(open_file_zscript)
        return filepath

    def save_workfile(self, filepath=None):
        if not filepath:
            filepath = self.get_current_workfile()
        save_file_zscript = ("""
[IFreeze,
[MemCreate, currentfile, 100, 0]
[VarSet, filename, "{filepath}"]
[MemWriteString, currentfile, #filename, 0]
[FileNameSetNext, #filename]
[IKeyPress, 13, [IPress, File:Save:Save]]
]
""").format(filepath=filepath)
        context = get_global_context()
        save_current_workfile_context(context)

        execute_zscript(save_file_zscript)
        return filepath

    def work_root(self, session):
        return session["AVALON_WORKDIR"]

    def get_current_workfile(self):
        output_file = tempfile.NamedTemporaryFile(
            mode="w", prefix="a_zb_", suffix=".txt", delete=False
        )
        output_file.close()
        output_filepath = output_file.name.replace("\\", "/")
        find_current_filepath_zscript = ("""
[IFreeze,
[MemSaveToFile, currentfile, "{output_filepath}", 1]
[MemDelete, currentfile]
]
        """).format(output_filepath=output_filepath)
        execute_zscript(find_current_filepath_zscript)
        if not os.path.exists(output_filepath):
            return None
        with open(output_filepath, "r") as current_file:
            return str(current_file.read())

    def workfile_has_unsaved_changes(self):
        # Pop-up dialog would be located to ask if users
        # save scene if it has unsaved changes
        return None

    def get_workfile_extensions(self):
        return [".zpr"]

    def list_instances(self):
        """Get all OpenPype instances."""
        return get_workfile_metadata(ZBRUSH_SECTION_NAME_INSTANCES)

    def write_instances(self, data):
        return write_workfile_metadata(ZBRUSH_SECTION_NAME_INSTANCES, data)

    def get_containers(self):
        return get_containers()

    def application_exit(self):
        """Logic related to TimerManager.

        Todo:
            This should be handled out of Zbrush integration logic.
        """

        data = get_current_project_settings()
        stop_timer = data["tvpaint"]["stop_timer_on_application_exit"]

        if not stop_timer:
            return

        # Stop application timer.
        webserver_url = os.environ.get("OPENPYPE_WEBSERVER_URL")
        rest_api_url = "{}/timers_manager/stop_timer".format(webserver_url)
        requests.post(rest_api_url)

    def update_context_data(self, data, changes):
        return write_workfile_metadata(ZBRUSH_METADATA_CREATE_CONTEXT, data)

    def get_context_data(self):
        get_workfile_metadata(ZBRUSH_METADATA_CREATE_CONTEXT, {})

def containerise(
        name, namespace, context, loader, containers=None):
    data = {
        "schema": "openpype:container-2.0",
        "id": AVALON_CONTAINER_ID,
        "name": name,
        "namespace": namespace or "",
        "loader": str(loader),
        "representation": str(context["representation"]["_id"]),
    }
    if containers is None:
        containers = get_containers()

    containers.append(data)

    write_workfile_metadata(ZBRUSH_SECTION_NAME_CONTAINERS, containers)

    return data


def write_workfile_metadata(metadata_key, value):
    data_dict = {metadata_key: value}
    context_data_zscript = ("""
[IFreeze,
[MemCreate, ayonData, 4000, 0]
[MemWriteString, ayonData, {data}, 0]
]
""").format(data=data_dict)
    execute_zscript(context_data_zscript)


def get_current_workfile_context():
    return get_workfile_metadata(ZBRUSH_SECTION_NAME_CONTEXT, {})


def save_current_workfile_context(context):
    return write_workfile_metadata(ZBRUSH_SECTION_NAME_CONTEXT, context)


def get_workfile_metadata(metadata_key, default=None):
    if default is None:
        default = "[]"
    data_dict = {metadata_key: default}
    output_file = tempfile.NamedTemporaryFile(
        mode="w", prefix="a_zb_", suffix=".txt", delete=False
    )
    output_file.close()
    output_filepath = output_file.name.replace("\\", "/")
    context_data_zscript = ("""
[IFreeze,
[If, [MemCreate, ayonData, 4000, 0] !=-1,
[MemCreate, ayonData, 4000, 0]
[MemWriteString, ayonData, {data}, 0]]
[MemSaveToFile, ayonData, "{output_filepath}", 1]
[MemDelete, ayonData]
]
""").format(data=data_dict, output_filepath=output_filepath)
    execute_zscript(context_data_zscript)
    with open(output_filepath) as data:
        file_content = str(data.read().strip()).rstrip('\x00')
        file_content = ast.literal_eval(file_content)
    return file_content


def get_containers():
    output = get_workfile_metadata(ZBRUSH_SECTION_NAME_CONTAINERS)
    if output:
        for item in output:
            if "objectName" not in item and "members" in item:
                members = item["members"]
                if isinstance(members, list):
                    members = "|".join([str(member) for member in members])
                item["objectName"] = members
    return output
