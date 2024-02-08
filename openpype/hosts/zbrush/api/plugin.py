from openpype.pipeline import CreatedInstance, Creator, AutoCreator
from openpype.pipeline.create.creator_plugins import cache_and_get_instances

SHARED_DATA_KEY = "openpype.zbrush.instances"

class ZbrushCreatorBase:
    def _cache_and_get_instances(self):
        return cache_and_get_instances(
            self, SHARED_DATA_KEY, self.host.list_instances
        )

    def _update_instances(self, update_list):
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

    def collect_instances(self):
        instances_by_identifier = self._cache_and_get_instances()
        for instance_data in instances_by_identifier[self.identifier]:
            instance = CreatedInstance.from_existing(instance_data, self)
            self._add_instance_to_context(instance)


class ZbrushCreator(Creator):

    def collect_instances(self):
        self._collect_instances()

    def update_instances(self, update_list):
        self._update_instances(update_list)

    def remove_instances(self, instances):
        ids_to_remove = {
            instance.id
            for instance in instances
        }
        cur_instances = self.host.list_instances()
        changed = False
        new_instances = []
        for instance_data in cur_instances:
            if instance_data.get("instance_id") in ids_to_remove:
                changed = True
            else:
                new_instances.append(instance_data)

        if changed:
            self.host.write_instances(new_instances)

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

    def _store_new_instance(self, new_instance):
        instances_data = self.host.list_instances()
        instances_data.append(new_instance.data_to_store())
        self.host.write_instances(instances_data)
        self._add_instance_to_context(new_instance)

class ZbrushAutoCreator(AutoCreator, ZbrushCreatorBase):
    def collect_instances(self):
        self._collect_create_instances()

    def update_instances(self, update_list):
        self._update_create_instances(update_list)
