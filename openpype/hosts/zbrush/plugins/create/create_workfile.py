# -*- coding: utf-8 -*-
"""Creator plugin for creating workfiles."""
from openpype import AYON_SERVER_ENABLED
from openpype.pipeline import CreatedInstance
from openpype.client import get_asset_by_name, get_asset_name_identifier
from openpype.hosts.zbrush.api import plugin

class CreateWorkfile(plugin.ZbrushAutoCreator):
    """Workfile auto-creator."""
    identifier = "io.openpype.creators.zbrush.workfile"
    label = "Workfile"
    family = "workfile"
    icon = "fa5.file"

    default_variant = "Main"

    def create(self):
        variant = self.default_variant
        current_instance = next(
            (
                instance for instance in self.create_context.instances
                if instance.creator_identifier == self.identifier
            ), None)
        project_name = self.project_name
        asset_name = self.create_context.get_current_asset_name()
        task_name = self.create_context.get_current_task_name()
        host_name = self.create_context.host_name

        if current_instance is None:
            current_instance_asset = None
        elif AYON_SERVER_ENABLED:
            current_instance_asset = current_instance["folderPath"]
        else:
            current_instance_asset = current_instance["asset"]

        if current_instance is None:
            asset_doc = get_asset_by_name(project_name, asset_name)
            subset_name = self.get_subset_name(
                variant, task_name, asset_doc, project_name, host_name
            )
            data = {
                "task": task_name,
                "variant": variant
            }
            if AYON_SERVER_ENABLED:
                data["folderPath"] = asset_name
            else:
                data["asset"] = asset_name

            new_instance = CreatedInstance(
                self.family, subset_name, data, self
            )
            instances_data = self.host.list_instances()
            instances_data.append(new_instance.data_to_store())
            self.host.write_instances(instances_data)
            self._add_instance_to_context(new_instance)

        elif (
            current_instance_asset != asset_name
            or current_instance["task"] != task_name
        ):
            # Update instance context if is not the same
            asset_doc = get_asset_by_name(project_name, asset_name)
            subset_name = self.get_subset_name(
                variant, task_name, asset_doc, project_name, host_name
            )
            asset_name = get_asset_name_identifier(asset_doc)

            if AYON_SERVER_ENABLED:
                current_instance["folderPath"] = asset_name
            else:
                current_instance["asset"] = asset_name
            current_instance["task"] = task_name
            current_instance["subset"] = subset_name
