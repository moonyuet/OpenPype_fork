import os
from pathlib import Path
import sys
import time
import collections
import platform
import traceback
from qtpy import QtWidgets, QtCore
from types import ModuleType
from typing import Dict, List, Optional, Union
from openpype.tools.utils import host_tools
from openpype import style
from openpype import AYON_SERVER_ENABLED
from openpype.pipeline import get_current_asset_name, get_current_task_name
TIMER_INTERVAL: float = 0.01 if platform.system() == "Windows" else 0.1


class ZbrushApplication(QtWidgets.QApplication):
    _instance = None
    zwindows = {}

    def __init__(self, *args, **kwargs):
        super(ZbrushApplication, self).__init__(*args, **kwargs)
        self.setQuitOnLastWindowClosed(False)

        self.setStyleSheet(style.load_stylesheet())
        self.lastWindowClosed.connect(self.__class__.reset)

    @classmethod
    def get_app(cls):
        if cls._instance is None:
            cls._instance = cls(sys.argv)
        return cls._instance

    @classmethod
    def reset(cls):
        cls._instance = None

    @classmethod
    def store_window(cls, tool_name, window):
        current_window = cls.get_window(tool_name)
        cls.blender_windows[tool_name] = window
        if current_window:
            current_window.close()

    @classmethod
    def get_window(cls, tool_name):
        return cls.zwindows.get(tool_name)


class LaunchQtApp:
    """A Base class for opertors to launch a Qt app."""

    _app: QtWidgets.QApplication
    _window = Union[QtWidgets.QDialog, ModuleType]
    _tool_name: str = None
    _init_args: Optional[List] = list()
    _init_kwargs: Optional[Dict] = dict()

    def __init__(self):
        if self._tool_name is None:
            raise NotImplementedError("Attribute `bl_idname` must be set!")
        print(f"Initialising {self._tool_name}...")
        self._app = ZbrushApplication.get_app()
        GlobalClass.app = self._app
        timer = QtCore.QTimer()
        timer.setInterval(100)
        timer.timeout.connect(_process_app_events)
        timer.start()

    def launch(self):

        if self._tool_name is None:
            if self._window is None:
                raise AttributeError("`self._window` is not set.")

        else:
            window = self._app.get_window(self._tool_name)
            if window is None:
                window = host_tools.get_tool_by_name(self._tool_name)
                self._app.store_window(self._tool_name, window)
            self._window = window

        if not isinstance(self._window, (QtWidgets.QWidget, ModuleType)):
            raise AttributeError(
                "`window` should be a `QWidget or module`. Got: {}".format(
                    str(type(window))
                )
            )

        self.before_window_show()

        def pull_to_front(window):
            """Pull window forward to screen.

            If Window is minimized this will un-minimize, then it can be raised
            and activated to the front.
            """
            window.setWindowState(
                (window.windowState() & ~QtCore.Qt.WindowMinimized) |
                QtCore.Qt.WindowActive
            )
            window.raise_()
            window.activateWindow()

        if isinstance(self._window, ModuleType):
            self._window.show()
            pull_to_front(self._window)

            # Pull window to the front
            window = None
            if hasattr(self._window, "window"):
                window = self._window.window
            elif hasattr(self._window, "_window"):
                window = self._window.window

            if window:
                self._app.store_window(self._tool_name, window)

        else:
            origin_flags = self._window.windowFlags()
            on_top_flags = origin_flags | QtCore.Qt.WindowStaysOnTopHint
            self._window.setWindowFlags(on_top_flags)
            self._window.show()
            pull_to_front(self._window)

        return

    def before_window_show(self):
        return

class GlobalClass:
    app = None
    main_thread_callbacks = collections.deque()
    is_windows = platform.system().lower() == "windows"

def execute_in_main_thread(main_thead_item):
    print("execute_in_main_thread")
    GlobalClass.main_thread_callbacks.append(main_thead_item)


def _process_app_events() -> Optional[float]:
    """Process the events of the Qt app if the window is still visible.

    If the app has any top level windows and at least one of them is visible
    return the time after which this function should be run again. Else return
    None, so the function is not run again and will be unregistered.
    """
    while GlobalClass.main_thread_callbacks:
        main_thread_item = GlobalClass.main_thread_callbacks.popleft()
        main_thread_item.execute()
        if main_thread_item.exception is not MainThreadItem.not_set:
            _clc, val, tb = main_thread_item.exception
            msg = str(val)
            detail = "\n".join(traceback.format_exception(_clc, val, tb))
            dialog = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                "Error",
                msg)
            dialog.setMinimumWidth(500)
            dialog.setDetailedText(detail)
            dialog.exec_()

        # Refresh Manager
        if GlobalClass.app:
            manager = GlobalClass.app.get_window("WM_OT_avalon_manager")
            if manager:
                manager.refresh()

    if not GlobalClass.is_windows:
        app = GlobalClass.app
        if app._instance:
            app.processEvents()
            return TIMER_INTERVAL
    return TIMER_INTERVAL


class MainThreadItem:
    """Structure to store information about callback in main thread.

    Item should be used to execute callback in main thread which may be needed
    for execution of Qt objects.

    Item store callback (callable variable), arguments and keyword arguments
    for the callback. Item hold information about it's process.
    """
    not_set = object()
    sleep_time = 0.1

    def __init__(self, callback, *args, **kwargs):
        self.done = False
        self.exception = self.not_set
        self.result = self.not_set
        self.callback = callback
        self.args = args
        self.kwargs = kwargs

    def execute(self):
        """Execute callback and store its result.

        Method must be called from main thread. Item is marked as `done`
        when callback execution finished. Store output of callback of exception
        information when callback raises one.
        """
        print("Executing process in main thread")
        if self.done:
            print("- item is already processed")
            return

        callback = self.callback
        args = self.args
        kwargs = self.kwargs
        print("Running callback: {}".format(str(callback)))
        try:
            result = callback(*args, **kwargs)
            self.result = result

        except Exception:
            self.exception = sys.exc_info()

        finally:
            print("Done")
            self.done = True

    def wait(self):
        """Wait for result from main thread.

        This method stops current thread until callback is executed.

        Returns:
            object: Output of callback. May be any type or object.

        Raises:
            Exception: Reraise any exception that happened during callback
                execution.
        """
        while not self.done:
            print(self.done)
            time.sleep(self.sleep_time)

        if self.exception is self.not_set:
            return self.result
        raise self.exception


class LaunchCreator(LaunchQtApp):
    """Launch Avalon Creator."""

    _tool_name = "creator"

    def before_window_show(self):
        self._window.refresh()

    def launch(self):
        host_tools.show_publisher(tab="create")


class LaunchLoader(LaunchQtApp):
    """Launch Avalon Creator."""

    _tool_name = "loader"

    def before_window_show(self):
        if AYON_SERVER_ENABLED:
            return
        self._window.set_context(
            {"asset": get_current_asset_name()},
            refresh=True
        )

class LaunchPublisher(LaunchQtApp):
    """Launch Avalon Creator."""

    _tool_name = "creator"

    def before_window_show(self):
        self._window.refresh()

    def launch(self):
        host_tools.show_publisher(tab="publish")


class LaunchSceneInventory(LaunchQtApp):
    """Launch Avalon Manager."""

    _tool_name = "sceneinventory"

    def before_window_show(self):
        if AYON_SERVER_ENABLED:
            return
        self._window.refresh()
    def launch(self):
        host_tools.show_scene_inventory()


class LaunchWorkFiles(LaunchQtApp):
    """Launch Avalon Work Files."""

    _tool_name = "workfiles"

    def execute(self, context):
        result = super().execute(context)
        if not AYON_SERVER_ENABLED:
            self._window.set_context({
                "asset": get_current_asset_name(),
                "task": get_current_task_name()
            })
        return result

    def before_window_show(self):
        if AYON_SERVER_ENABLED:
            return
        self._window.root = str(Path(
            os.environ.get("AVALON_WORKDIR", ""),
            os.environ.get("AVALON_SCENEDIR", ""),
        ))
        self._window.refresh()
