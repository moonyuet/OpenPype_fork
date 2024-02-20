"""Pipeline tools for OpenPype Zbrush integration."""
import os
import ast
import json
import shutil
import logging
import requests
import tempfile
import pyblish.api
from openpype.host import HostBase, IWorkfileHost, ILoadHost, IPublishHost
from openpype.pipeline import (
    legacy_io,
    register_creator_plugin_path,
    register_loader_plugin_path,
    AVALON_CONTAINER_ID
)
from openpype.pipeline.context_tools import get_global_context

from openpype.settings import get_current_project_settings
from openpype.lib import register_event_callback
from openpype.hosts.zbrush import ZBRUSH_HOST_DIR
from .lib import execute_zscript, get_workdir, get_current_file

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

        register_event_callback("application.launched", self.initial_app_launch)
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
[MemDelete, currentfile]
]
    """).format(filepath=filepath)
        execute_zscript(open_file_zscript)
        set_current_file(filepath=filepath)
        return filepath

    def save_workfile(self, filepath):
        if not filepath:
            filepath = self.get_current_workfile()
        filepath = filepath.replace("\\", "/")
        save_file_zscript = ("""
[IFreeze,
[MemCreate, currentfile, 1000, 0]
[VarSet, filename, "{filepath}"]
[MemWriteString, currentfile, #filename, 0]
[FileNameSetNext, #filename]
[IKeyPress, 13, [IPress, File:SaveAs:SaveAs]]]
[MemDelete, currentfile]
]
""").format(filepath=filepath)
        context = get_global_context()
        save_current_workfile_context(context)
        # move the json data to the files
        # shutil.copy
        copy_ayon_data(filepath)
        set_current_file(filepath=filepath)
        execute_zscript(save_file_zscript)
        return filepath

    def work_root(self, session):
        return session["AVALON_WORKDIR"]

    def get_current_workfile(self):
        project_name = get_current_context()["project_name"]
        asset_name = get_current_context()["asset_name"]
        task_name = get_current_context()["task_name"]
        work_dir = get_workdir(project_name, asset_name, task_name)
        txt_dir = os.path.join(
            work_dir, ".zbrush_metadata").replace(
                "\\", "/"
        )
        with open (f"{txt_dir}/current_file.txt", "r") as current_file:
            content = str(current_file.read())
            filepath = content.rstrip('\x00')
            current_file.close()
            return filepath


    def workfile_has_unsaved_changes(self):
        # Pop-up dialog would be located to ask if users
        # save scene if it has unsaved changes
        return False

    def get_workfile_extensions(self):
        return [".zpr"]

    def list_instances(self):
        """Get all OpenPype instances."""
        return get_workfile_metadata(ZBRUSH_SECTION_NAME_INSTANCES)

    def write_instances(self, data):
        return write_workfile_metadata(ZBRUSH_SECTION_NAME_INSTANCES, data)

    def get_containers(self):
        return get_containers()

    def initial_app_launch(self):
        #TODO: figure out how to deal with the last workfile issue
        set_current_file()

    def application_exit(self):
        """Logic related to TimerManager.

        Todo:
            This should be handled out of Zbrush integration logic.
        """
        remove_tmp_data(ZBRUSH_SECTION_NAME_CONTAINERS)
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
        name, context, namespace="", loader=None, containers=None):
    data = {
        "schema": "openpype:container-2.0",
        "id": AVALON_CONTAINER_ID,
        "name": name,
        "namespace": namespace,
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
    current_context = get_current_context()
    return get_workfile_metadata(ZBRUSH_SECTION_NAME_CONTEXT, current_context)


def get_current_context():
    return {
        "project_name": os.environ.get("AVALON_PROJECT"),
        "asset_name": os.environ.get("AVALON_ASSET"),
        "task_name": os.environ.get("AVALON_TASK"),
    }


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
            if "objectName" not in item and "name" in item:
                members = item["name"]
                if isinstance(members, list):
                    members = "|".join([str(member) for member in members])
                item["objectName"] = members

    return output

def write_load_metadata(metadata_key, data):
    #TODO: create temp json file
    project_name = get_current_context()["project_name"]
    asset_name = get_current_context()["asset_name"]
    task_name = get_current_context()["task_name"]
    current_file = get_current_file()
    if current_file:
        current_file = os.path.splitext(
            os.path.basename(current_file))[0].strip()
    work_dir = get_workdir(project_name, asset_name, task_name)
    name = next((d["name"] for d in data), None)
    json_dir = os.path.join(
        work_dir, ".zbrush_metadata",
        current_file, metadata_key).replace(
            "\\", "/"
        )
    os.makedirs(json_dir, exist_ok=True)
    with open (f"{json_dir}/{name}.json", "w") as file:
        value = json.dumps(data)
        file.write(value)
        file.close()


def get_load_workfile_metadata(metadata_key):
    # save zscript to the hidden folder
    # load json files
    file_content = []
    project_name = get_current_context()["project_name"]
    asset_name = get_current_context()["asset_name"]
    task_name = get_current_context()["task_name"]
    current_file = get_current_file()
    if current_file:
        current_file = os.path.splitext(
            os.path.basename(current_file))[0].strip()
    work_dir = get_workdir(project_name, asset_name, task_name)
    json_dir = os.path.join(
        work_dir, ".zbrush_metadata",
        current_file, metadata_key).replace(
            "\\", "/"
        )
    if not os.path.exists(json_dir):
        return file_content
    file_list = os.listdir(json_dir)
    if not file_list:
        return file_content
    for file in file_list:
        with open (f"{json_dir}/{file}", "r") as data:
            content = ast.literal_eval(str(data.read().strip()))
            file_content.extend(content)
            data.close()
    return file_content


def remove_container_data(name):
    project_name = get_current_context()["project_name"]
    asset_name = get_current_context()["asset_name"]
    task_name = get_current_context()["task_name"]
    current_file = get_current_file()
    if current_file:
        current_file = os.path.splitext(
            os.path.basename(current_file))[0].strip()
    work_dir = get_workdir(project_name, asset_name, task_name)
    json_dir = os.path.join(
        work_dir, ".zbrush_metadata",
        current_file, ZBRUSH_SECTION_NAME_CONTAINERS).replace(
            "\\", "/"
        )
    all_fname_list = os.listdir(json_dir)
    json_file = next((jfile for jfile in all_fname_list
                               if jfile == f"{name}.json"), None)
    if json_file:
        os.remove(f"{json_dir}/{json_file}")


def remove_tmp_data(name):
    project_name = get_current_context()["project_name"]
    asset_name = get_current_context()["asset_name"]
    task_name = get_current_context()["task_name"]
    work_dir = get_workdir(project_name, asset_name, task_name)
    json_dir = os.path.join(
        work_dir, ".zbrush_metadata", name).replace(
            "\\", "/"
        )
    all_fname_list = [jfile for jfile in os.listdir(json_dir)
                if jfile.endswith("json")]
    for fname in all_fname_list:
        os.remove(f"{json_dir}/{fname}")


def copy_ayon_data(filepath):
    filename = os.path.splitext(os.path.basename(filepath))[0].strip()
    project_name = get_current_context()["project_name"]
    asset_name = get_current_context()["asset_name"]
    task_name = get_current_context()["task_name"]
    current_file = get_current_file()
    if current_file:
        current_file = os.path.splitext(
            os.path.basename(current_file))[0].strip()
    work_dir = get_workdir(project_name, asset_name, task_name)
    name = ZBRUSH_SECTION_NAME_CONTAINERS
    src_json_dir = os.path.join(
        work_dir, ".zbrush_metadata", current_file, name).replace(
            "\\", "/"
        )
    dst_json_dir = os.path.join(
        work_dir, ".zbrush_metadata", filename, name).replace(
            "\\", "/"
        )
    os.makedirs(dst_json_dir, exist_ok=True)
    all_fname_list = [jfile for jfile in os.listdir(src_json_dir)
                      if jfile.endswith("json")]
    if all_fname_list:
        for fname in all_fname_list:
            src_json = f"{src_json_dir}/{fname}"
            dst_json = f"{dst_json_dir}/{fname}"
            shutil.copy(src_json, dst_json)


def set_current_file(filepath=None):
    project_name = get_current_context()["project_name"]
    asset_name = get_current_context()["asset_name"]
    task_name = get_current_context()["task_name"]
    work_dir = get_workdir(project_name, asset_name, task_name)
    txt_dir = os.path.join(
        work_dir, ".zbrush_metadata").replace(
            "\\", "/"
    )
    txt_file = f"{txt_dir}/current_file.txt"
    if filepath is None:
        with open(txt_file, 'w'): pass
        return filepath

    with open (txt_file, "w") as current_file:
        current_file.write(filepath)
        current_file.close()


def imprint(container, representation_id):
    data = []
    name = container["objectName"]
    project_name = get_current_context()["project_name"]
    asset_name = get_current_context()["asset_name"]
    task_name = get_current_context()["task_name"]
    current_file = get_current_file()
    if current_file:
        current_file = os.path.splitext(
            os.path.basename(current_file))[0].strip()
    work_dir = get_workdir(project_name, asset_name, task_name)
    json_dir = os.path.join(
        work_dir, ".zbrush_metadata",
        current_file, ZBRUSH_SECTION_NAME_CONTAINERS).replace(
            "\\", "/"
        )
    js_fname = next((jfile for jfile in os.listdir(json_dir)
                     if jfile.endswith(f"{name}.json")), None)
    if js_fname:
        with open(f"{json_dir}/{js_fname}", "r") as file:
            data = json.load(file)
            file.truncate()
            file.close()
        data["representation"] = representation_id
        with open(f"{json_dir}/{js_fname}", "w") as file:
            data = json.dumps(data)
            file.write(data)
            file.close()
