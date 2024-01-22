# -*- coding: utf-8 -*-
"""Pre-launch to force zbrush startup script."""
import os
from openpype.hosts.zbrush import ZBRUSH_HOST_DIR
from openpype.lib.applications import PreLaunchHook, LaunchTypes


class ForceStartupScript(PreLaunchHook):
    """Inject OpenPype environment to Zbrush.

    Note that this works in combination whit Zbrush startup script that
    is creating the environment variable for the Openpype Plugin

    Hook `GlobalHostDataHook` must be executed before this hook.
    """
    app_groups = {"zbrush"}
    order = 11
    launch_types = {LaunchTypes.local}

    def execute(self):
        startup_args = [
            os.path.join(ZBRUSH_HOST_DIR, "startup", "startup.txt"),
        ]
        self.launch_context.launch_args.append(startup_args)
