from openpype.pipeline import CreatedInstance, Creator, get_subset_name
from openpype.lib import BoolDef
from openpype.hosts.substancepainter.api.pipeline import (
    get_instances,
    set_instance,
    set_instances,
    remove_instance
)
from openpype.pipeline.create.creator_plugins import cache_and_get_instances

SHARED_DATA_KEY = "openpype.zbrush.instances"


class ZbrushCreator(Creator):

    def create(self, subset_name, instance_data, pre_create_data):
        if pre_create_data.get("use_selection"):
            pass

        instance_node = self.create_instance_node(subset_name)
        instance_data["instance_node"] = instance_node
        instance = CreatedInstance(
            self.family,
            subset_name,
            instance_data,
            self
        )

        return instance

    def _cache_and_get_instances(self):
        return cache_and_get_instances(
            self, SHARED_DATA_KEY, self.host.list_instances
        )

    def collect_instances(self):
        instances_by_identifier = self._cache_and_get_instances()
        for instance_data in instances_by_identifier[self.identifier]:
            instance = CreatedInstance.from_existing(instance_data, self)
            self._add_instance_to_context(instance)

    def update_instances(self, update_list):
        if not update_list:
            return
        current_instances = self.host.list_instances()
        cur_instances_by_id = {}
        for instance_data in current_instances:
            instance_id = instance_data.get("instance_id")
            if instance_id:
                cur_instances_by_id[instance_id] = instance_data

        for instance, changes in update_list:
            instance_data = changes.new_value
            cur_instance_data = cur_instances_by_id.get(instance.id)
            if cur_instance_data is None:
                current_instances.append(instance_data)
                continue
            for key in set(cur_instance_data) - set(instance_data):
                cur_instance_data.pop(key)
            cur_instance_data.update(instance_data)
        self.host.write_instances(current_instances)

    def remove_instances(self, instances):
        """Remove specified instance from the scene.

        This is only removing `id` parameter so instance is no longer
        instance, because it might contain valuable data for artist.

        """
        for instance in instances:

            self._remove_instance_from_context(instance)
    # Helper methods (this might get moved into Creator class)
    def get_dynamic_data(self, *args, **kwargs):
        # Change asset and name by current workfile context
        create_context = self.create_context
        asset_name = create_context.get_current_asset_name()
        task_name = create_context.get_current_task_name()
        output = {}
        if asset_name:
            output["asset"] = asset_name
            if task_name:
                output["task"] = task_name
        return output

    def get_subset_name(self, *args, **kwargs):
        return self._custom_get_subset_name(*args, **kwargs)

    def _store_new_instance(self, new_instance):
        instances_data = self.host.list_instances()
        instances_data.append(new_instance.data_to_store())
        self.host.write_instances(instances_data)
        self._add_instance_to_context(new_instance)

    def _custom_get_subset_name(
        self,
        variant,
        task_name,
        asset_doc,
        project_name,
        host_name=None,
        instance=None
    ):
        dynamic_data = self.get_dynamic_data(
            variant, task_name, asset_doc, project_name, host_name, instance
        )

        return get_subset_name(
            self.family,
            variant,
            task_name,
            asset_doc,
            project_name,
            host_name,
            dynamic_data=dynamic_data,
            project_settings=self.project_settings,
            family_filter=self.subset_template_family_filter
        )
