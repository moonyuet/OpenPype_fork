#zscript command etc.
import os
import logging
import tempfile
from openpype.lib import run_subprocess


log = logging.getLogger("zbrush.lib")


def execute_zscript(zscript):
    zbrush_exe = os.environ["ZBRUSH_EXE"]
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        tmp_script_path = os.path.join(
            tmp_dir_name, "temp_execute_zscript.py")
        scripts = [zscript]
        with open(tmp_script_path, "wt") as tmp:
            for script in scripts:
                tmp.write(script + "\n")
        try:
            tmp_script_path = tmp_script_path.replace("\\", "/")
            run_subprocess([zbrush_exe, tmp_script_path])
        except RuntimeError:
            log.debug("Checking the scene files existing")
