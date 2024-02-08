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
        context = get_global_context()
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
[MemCreate, currentfile, 1000, 0]
[VarSet, filename, "{filepath}"]
[MemWriteString, currentfile, #filename, 0]
[FileNameSetNext, #filename]
[IKeyPress, 13, [IPress, File:Open:Open]]]
]
    """).format(filepath=filepath)
        execute_zscript(open_file_zscript)
        return filepath

    def save_workfile(self, filepath):
        if not filepath:
            filepath = self.get_current_workfile()
        filepath = filepath.replace("\\", "/")
        save_file_zscript = ("""
[IFreeze,
[If, [MemCreate, currentfile, 1000, 0] !=-1,
[MemCreate, currentfile]]
[VarSet, filename, "{filepath}"]
[MemWriteString, currentfile, #filename, 0]
[FileNameSetNext, #filename]
[IKeyPress, 13, [IPress, File:SaveAs:SaveAs]]
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
[MemCreate, currentfile, 1000, 0]
[MemSaveToFile, currentfile, "{output_filepath}", 1]
]
        """).format(output_filepath=output_filepath)
        execute_zscript(find_current_filepath_zscript)
        if not os.path.exists(output_filepath):
            return None
        with open(output_filepath, "r") as current_file:
            return str(current_file.read()).rstrip('\x00')

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
        name, namespace, context, loader=None, containers=None):
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

    write_load_metadata(ZBRUSH_SECTION_NAME_CONTAINERS, containers)
    return data


def write_workfile_metadata(metadata_key, value):
    context_data_zscript = ("""
[IFreeze,
[MemCreate, {metadata_key}, 400000, 0]
[MemWriteString, {metadata_key}, "{data}", 0]
]
""").format(metadata_key=metadata_key, data=value)
    return execute_zscript(context_data_zscript)


def get_current_workfile_context():
    current_context = {
        "project_name": os.environ.get("AVALON_PROJECT"),
        "asset_name": os.environ.get("AVALON_ASSET"),
        "task_name": os.environ.get("AVALON_TASK"),
    }
    return get_workfile_metadata(ZBRUSH_SECTION_NAME_CONTEXT, current_context)


def save_current_workfile_context(context):
    return write_workfile_metadata(ZBRUSH_SECTION_NAME_CONTEXT, context)


def get_workfile_metadata(metadata_key, default=None):
    if default is None:
        default = []
    output_file = tempfile.NamedTemporaryFile(
        mode="w", prefix="a_zb_meta", suffix=".txt", delete=False
    )
    output_file.close()
    output_filepath = output_file.name.replace("\\", "/")
    context_data_zscript = ("""
[IFreeze,
[If, [MemCreate, {metadata_key}, 400000, 0] !=-1,
[MemCreate, {metadata_key}, 400000, 0]
[MemWriteString, {metadata_key}, "{default}", 0]]
[MemSaveToFile, {metadata_key}, "{output_filepath}", 1]
[MemDelete, {metadata_key}]
]
""").format(metadata_key=metadata_key,
            default=default, output_filepath=output_filepath)
    execute_zscript(context_data_zscript)
    with open(output_filepath) as data:
        file_content = str(data.read().strip()).rstrip('\x00')
        file_content = ast.literal_eval(file_content)
    return file_content


def get_containers():
    output = get_load_workfile_metadata(ZBRUSH_SECTION_NAME_CONTAINERS)
    if output:
        for item in output:
            if "objectName" not in item and "members" in item:
                members = item["members"]
                if isinstance(members, list):
                    members = "|".join([str(member) for member in members])
                item["objectName"] = members
    return output

def write_load_metadata(metadata_key, data):
    #TODO: create temp json file
    string_list = []
    if data:
        for key, value in data.items():
            string_dict = {key : value}
            string = ("""
[MemCreate, {metadata_key}_{key}, 40000, 0]
[MemWriteString, {metadata_key}_{key}, "{string_dict}", 0]
    """).format(metadata_key=metadata_key, key=key, string_dict=string_dict)
            string_list.append(string)
        context_data_zscript = ("""
[IFreeze,
[MemCreate, {metadata_key}, 400000, 0]
{memstring}
]
""").format(metadata_key=metadata_key, memstring=listToString(string_list))
        execute_zscript(context_data_zscript)
    else:
        context_data_zscript = ("""
[IFreeze,
[MemCreate, {metadata_key}, 400000, 0]
{memstring}
]
""").format(metadata_key=metadata_key, memstring=listToString(string_list))
        execute_zscript(context_data_zscript)


def get_load_workfile_metadata(metadata_key, default=None):
    if default is None:
        default = []
        output_file = tempfile.NamedTemporaryFile(
            mode="w", prefix="a_zb_meta", suffix=".txt", delete=False
        )
        output_file.close()
        output_filepath = output_file.name.replace("\\", "/")
        context_data_zscript = ("""
[IFreeze,
[If, [MemCreate, {metadata_key}, 400000, 0] !=-1,
[MemCreate, {metadata_key}, 400000, 0]
[MemWriteString, {metadata_key}, "{default}", 0]]
[MemSaveToFile, {metadata_key}, "{output_filepath}", 1]
[MemDelete, {metadata_key}]
]
    """).format(metadata_key=metadata_key,
                default=default, output_filepath=output_filepath)
        execute_zscript(context_data_zscript)
        with open(output_filepath) as data:
            file_content = str(data.read().strip()).rstrip('\x00')
            file_content = ast.literal_eval(file_content)
        return file_content


def load_metadata_with_list(metadata_key, container_data):
    zstring_list = []
    data = {}
    output_filepath_list = []
    for data in container_data:
        for key in data.keys():
            output_file = tempfile.NamedTemporaryFile(
                mode="w", prefix=f"a_zb_{key}", suffix=".txt", delete=False
            )
            output_file.close()
            output_filepath = output_file.name.replace("\\", "/")
            mem_string = ("""
[MemSaveToFile, {metadata_key}_{key}, "{output_filepath}", 1]
[MemDelete, {metadata_key}_{key}]
""").format(metadata_key=metadata_key, key=key, output_filepath=output_filepath)
            zstring_list.append(mem_string)
            output_filepath_list.append(output_filepath)
        context_data_zscript = ("""
[IFreeze,
{memstring}
]
""").format(memstring=listToString(zstring_list))
        execute_zscript(context_data_zscript)
        for filepath in output_filepath_list:
            with open(filepath) as data:
                file_content = str(data.read().strip()).rstrip('\x00')
                file_content = ast.literal_eval(file_content)
            data.update(file_content)
        return data


@staticmethod
def listToString(string_list):
    string = ""

    # traverse in the string
    for ele in string_list:
        string += f"{ele}\n"

    # return string
    return string
