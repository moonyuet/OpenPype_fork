#zscript command etc.
import os
import logging
from openpype.client import (
    get_project,
    get_asset_by_name,
)
from openpype.pipeline import Anatomy, registered_host
from string import Formatter
from . import CommunicationWrapper
from openpype.pipeline.template_data import get_template_data


log = logging.getLogger("zbrush.lib")


def execute_zscript(zscript, communicator=None):
    if not communicator:
        communicator = CommunicationWrapper.communicator
    return communicator.execute_zscript(zscript)

def find_first_filled_path(path):
    if not path:
        return ""

    fields = set()
    for item in Formatter().parse(path):
        _, field_name, format_spec, conversion = item
        if not field_name:
            continue
        conversion = "!{}".format(conversion) if conversion else ""
        format_spec = ":{}".format(format_spec) if format_spec else ""
        orig_key = "{{{}{}{}}}".format(
            field_name, conversion, format_spec)
        fields.add(orig_key)

    for field in fields:
        path = path.split(field, 1)[0]
    return path

def get_workdir(project_name, asset_name, task_name):
    project = get_project(project_name)
    asset = get_asset_by_name(project_name, asset_name)

    data = get_template_data(project, asset, task_name)

    anatomy = Anatomy(project_name)
    workdir = anatomy.templates_obj["work"]["folder"].format(data)

    # Remove any potential un-formatted parts of the path
    valid_workdir = find_first_filled_path(workdir)

    # Path is not filled at all
    if not valid_workdir:
        raise AssertionError("Failed to calculate workdir.")

    # Normalize
    valid_workdir = os.path.normpath(valid_workdir)
    if os.path.exists(valid_workdir):
        return valid_workdir

    data.pop("task", None)
    workdir = anatomy.templates_obj["work"]["folder"].format(data)
    valid_workdir = find_first_filled_path(workdir)
    if valid_workdir:
        # Normalize
        valid_workdir = os.path.normpath(valid_workdir)
        if os.path.exists(valid_workdir):
            return valid_workdir

def get_current_file():
    host = registered_host()
    return host.get_current_workfile()
