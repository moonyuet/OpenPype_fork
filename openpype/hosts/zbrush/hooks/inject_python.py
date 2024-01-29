# -*- coding: utf-8 -*-
"""Pre-launch hook to inject python environment."""
import os
from openpype.lib.applications import PreLaunchHook, LaunchTypes


class InjectPythonPath(PreLaunchHook):
    """Inject OpenPype environment to Zbrush.

    Note that this works in combination whit Zbrush startup script that
    is translating it back to PYTHONPATH for cases when Zbrush drops PYTHONPATH
    environment.

    Hook `GlobalHostDataHook` must be executed before this hook.
    """
    app_groups = {"zbrush"}
    launch_types = {LaunchTypes.local}

    def execute(self):
        self.launch_context.env["ZBRUSH_PLUGIN_PATH"] += os.environ["PYTHONPATH"]
