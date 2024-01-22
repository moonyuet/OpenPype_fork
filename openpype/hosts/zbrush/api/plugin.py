from openpype.pipeline import CreatedInstance, Creator
from openpype.lib import BoolDef
from openpype.hosts.substancepainter.api.pipeline import (
    get_instances,
    set_instance,
    set_instances,
    remove_instance
)
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

    def collect_instances(self):
        pass

    def update_instances(self, update_list):
        pass

    def remove_instances(self, instances):
        """Remove specified instance from the scene.

        This is only removing `id` parameter so instance is no longer
        instance, because it might contain valuable data for artist.

        """
        for instance in instances:

            self._remove_instance_from_context(instance)
    # Helper methods (this might get moved into Creator class)
    def create_instance_in_context(self, subset_name, data):
        instance = CreatedInstance(
            self.family, subset_name, data, self
        )
        self.create_context.creator_adds_instance(instance)
        return instance

    def create_instance_in_context_from_existing(self, data):
        instance = CreatedInstance.from_existing(data, self)
        self.create_context.creator_adds_instance(instance)
        return instance

    def get_pre_create_attr_defs(self):
        return [
            BoolDef("use_selection", label="Use selection")
        ]
