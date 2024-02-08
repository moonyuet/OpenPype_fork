import os
from openpype.pipeline import load
from openpype.hosts.zbrush.api.pipeline import containerise
from openpype.hosts.zbrush.api.lib import execute_zscript


class MeshLoader(load.LoaderPlugin):
    """Fbx Model Loader."""

    families = ["model"]
    representations = ["abc", "fbx", "obj", "ma"]
    order = -9
    icon = "code-fork"
    color = "white"

    def load(self, context, name=None, namespace=None, data=None):
        file_path = os.path.normpath(self.filepath_from_context(context))
        load_zscript = ("""
[IFreeze,
[VarSet, filename, "{filepath}"]
[FileNameSetNext, #filename]
[IKeyPress, 13, [IPress, Tool:Import:Import]]
]

""").format(filepath=file_path)
        execute_zscript(load_zscript)

        return containerise(
            name,
            namespace,
            context,
            loader=self.__class__.__name__)
