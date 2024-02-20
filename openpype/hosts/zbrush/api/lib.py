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

def unique_namespace(namespace, format="%02d",
                     prefix="", suffix="", con_suffix="CON"):
    """Return unique namespace

    Arguments:
        namespace (str): Name of namespace to consider
        format (str, optional): Formatting of the given iteration number
        suffix (str, optional): Only consider namespaces with this suffix.
        con_suffix: max only, for finding the name of the master container

    >>> unique_namespace("bar")
    # bar01
    >>> unique_namespace(":hello")
    # :hello01
    >>> unique_namespace("bar:", suffix="_NS")
    # bar01_NS:

    """

    def current_namespace():
        current = namespace
        # When inside a namespace Max adds no trailing :
        if not current.endswith(":"):
            current += ":"
        return current

    # Always check against the absolute namespace root
    # There's no clash with :x if we're defining namespace :a:x
    ROOT = ":" if namespace.startswith(":") else current_namespace()

    # Strip trailing `:` tokens since we might want to add a suffix
    start = ":" if namespace.startswith(":") else ""
    end = ":" if namespace.endswith(":") else ""
    namespace = namespace.strip(":")
    if ":" in namespace:
        # Split off any nesting that we don't uniqify anyway.
        parents, namespace = namespace.rsplit(":", 1)
        start += parents + ":"
        ROOT += start

    iteration = 1
    increment_version = True
    while increment_version:
        nr_namespace = namespace + format % iteration
        unique = prefix + nr_namespace + suffix
        container_name = f"{unique}:{namespace}{con_suffix}"
        if not rt.getNodeByName(container_name):
            name_space = start + unique + end
            increment_version = False
            return name_space
        else:
            increment_version = True
        iteration += 1
