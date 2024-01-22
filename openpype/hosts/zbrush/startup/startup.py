# -*- coding: utf-8 -*-
import os
import sys

# this might happen in some Zbrush version where PYTHONPATH isn't added
# to sys.path automatically
for path in os.environ["PYTHONPATH"].split(os.pathsep):
    if path and path not in sys.path:
        sys.path.append(path)

from openpype.hosts.zbrush.api import ZbrushHost
from openpype.pipeline import install_host

host = ZbrushHost()
install_host(host)
