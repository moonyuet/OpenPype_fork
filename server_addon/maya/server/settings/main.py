from pydantic import Field, validator
from ayon_server.settings import BaseSettingsModel, ensure_unique_names
from .imageio import ImageIOSettings, DEFAULT_IMAGEIO_SETTINGS
from .maya_dirmap import MayaDirmapModel, DEFAULT_MAYA_DIRMAP_SETTINGS
from .include_handles import IncludeHandlesModel, DEFAULT_INCLUDE_HANDLES
from .explicit_plugins_loading import (
    ExplicitPluginsLoadingModel, DEFAULT_EXPLITCIT_PLUGINS_LOADING_SETTINGS
)
from .scriptsmenu import ScriptsmenuModel, DEFAULT_SCRIPTSMENU_SETTINGS
from .render_settings import RenderSettingsModel, DEFAULT_RENDER_SETTINGS
from .creators import CreatorsModel, DEFAULT_CREATORS_SETTINGS
from .publishers import PublishersModel, DEFAULT_PUBLISH_SETTINGS
from .loaders import LoadersModel, DEFAULT_LOADERS_SETTING
from .workfile_build_settings import ProfilesModel, DEFAULT_WORKFILE_SETTING
from .templated_workfile_settings import (
    TemplatedProfilesModel, DEFAULT_TEMPLATED_WORKFILE_SETTINGS
)


class ExtMappingItemModel(BaseSettingsModel):
    _layout = "compact"
    name: str = Field(title="Product type")
    value: str = Field(title="Extension")


class MayaSettings(BaseSettingsModel):
    """Maya Project Settings."""

    open_workfile_post_initialization: bool = Field(
        True, title="Open Workfile Post Initialization")
    explicit_plugins_loading: ExplicitPluginsLoadingModel = Field(
        default_factory=ExplicitPluginsLoadingModel,
        title="Explicit Plugins Loading")
    imageio: ImageIOSettings = Field(
        default_factory=ImageIOSettings, title="Color Management (imageio)")
    mel_workspace: str = Field(title="Maya MEL Workspace", widget="textarea")
    ext_mapping: list[ExtMappingItemModel] = Field(
        default_factory=list, title="Extension Mapping")
    maya_dirmap: MayaDirmapModel = Field(
        default_factory=MayaDirmapModel, title="Maya dirmap Settings")
    include_handles: IncludeHandlesModel = Field(
        default_factory=IncludeHandlesModel,
        title="Include/Exclude Handles in default playback & render range"
    )
    scriptsmenu: ScriptsmenuModel = Field(
        default_factory=ScriptsmenuModel,
        title="Scriptsmenu Settings"
    )
    render_settings: RenderSettingsModel = Field(
        default_factory=RenderSettingsModel, title="Render Settings")
    create: CreatorsModel = Field(
        default_factory=CreatorsModel, title="Creators")
    publish: PublishersModel = Field(
        default_factory=PublishersModel, title="Publishers")
    load: LoadersModel = Field(
        default_factory=LoadersModel, title="Loaders")
    workfile_build: ProfilesModel = Field(
        default_factory=ProfilesModel, title="Workfile Build Settings")
    templated_workfile_build: TemplatedProfilesModel = Field(
        default_factory=TemplatedProfilesModel,
        title="Templated Workfile Build Settings")

    @validator("ext_mapping")
    def validate_unique_outputs(cls, value):
        ensure_unique_names(value)
        return value


DEFAULT_MEL_WORKSPACE_SETTINGS = "\n".join((
    'workspace -fr "shaders" "renderData/shaders";',
    'workspace -fr "images" "renders/maya";',
    'workspace -fr "particles" "particles";',
    'workspace -fr "mayaAscii" "";',
    'workspace -fr "mayaBinary" "";',
    'workspace -fr "scene" "";',
    'workspace -fr "alembicCache" "cache/alembic";',
    'workspace -fr "renderData" "renderData";',
    'workspace -fr "sourceImages" "sourceimages";',
    'workspace -fr "fileCache" "cache/nCache";',
    'workspace -fr "autoSave" "autosave";',
    '',
))

DEFAULT_MAYA_SETTING = {
    "open_workfile_post_initialization": True,
    "explicit_plugins_loading": DEFAULT_EXPLITCIT_PLUGINS_LOADING_SETTINGS,
    "imageio": DEFAULT_IMAGEIO_SETTINGS,
    "mel_workspace": DEFAULT_MEL_WORKSPACE_SETTINGS,
    "ext_mapping": [
        {"name": "model", "value": "ma"},
        {"name": "mayaAscii", "value": "ma"},
        {"name": "camera", "value": "ma"},
        {"name": "rig", "value": "ma"},
        {"name": "workfile", "value": "ma"},
        {"name": "yetiRig", "value": "ma"}
    ],
    # `maya_dirmap` was originally with dash - `maya-dirmap`
    "maya_dirmap": DEFAULT_MAYA_DIRMAP_SETTINGS,
    "include_handles": DEFAULT_INCLUDE_HANDLES,
    "scriptsmenu": DEFAULT_SCRIPTSMENU_SETTINGS,
    "render_settings": DEFAULT_RENDER_SETTINGS,
    "create": DEFAULT_CREATORS_SETTINGS,
    "publish": DEFAULT_PUBLISH_SETTINGS,
    "load": DEFAULT_LOADERS_SETTING,
    "workfile_build": DEFAULT_WORKFILE_SETTING,
    "templated_workfile_build": DEFAULT_TEMPLATED_WORKFILE_SETTINGS
}
