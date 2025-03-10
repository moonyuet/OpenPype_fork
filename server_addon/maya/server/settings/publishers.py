import json
from pydantic import Field, validator
from ayon_server.settings import (
    BaseSettingsModel,
    MultiplatformPathModel,
    ensure_unique_names,
)
from ayon_server.exceptions import BadRequestException
from .publish_playblast import (
    ExtractPlayblastSetting,
    DEFAULT_PLAYBLAST_SETTING,
)


def linear_unit_enum():
    """Get linear units enumerator."""
    return [
        {"label": "mm", "value": "millimeter"},
        {"label": "cm", "value": "centimeter"},
        {"label": "m", "value": "meter"},
        {"label": "km", "value": "kilometer"},
        {"label": "in", "value": "inch"},
        {"label": "ft", "value": "foot"},
        {"label": "yd", "value": "yard"},
        {"label": "mi", "value": "mile"}
    ]


def angular_unit_enum():
    """Get angular units enumerator."""
    return [
        {"label": "deg", "value": "degree"},
        {"label": "rad", "value": "radian"},
    ]


class BasicValidateModel(BaseSettingsModel):
    enabled: bool = Field(title="Enabled")
    optional: bool = Field(title="Optional")
    active: bool = Field(title="Active")


class ValidateMeshUVSetMap1Model(BasicValidateModel):
    """Validate model's default uv set exists and is named 'map1'."""
    pass


class ValidateNoAnimationModel(BasicValidateModel):
    """Ensure no keyframes on nodes in the Instance."""
    pass


class ValidateRigOutSetNodeIdsModel(BaseSettingsModel):
    enabled: bool = Field(title="ValidateSkinclusterDeformerSet")
    optional: bool = Field(title="Optional")
    allow_history_only: bool = Field(title="Allow history only")


class ValidateModelNameModel(BaseSettingsModel):
    enabled: bool = Field(title="Enabled")
    database: bool = Field(title="Use database shader name definitions")
    material_file: MultiplatformPathModel = Field(
        default_factory=MultiplatformPathModel,
        title="Material File",
        description=(
            "Path to material file defining list of material names to check."
        )
    )
    regex: str = Field(
        "(.*)_(\\d)*_(?P<shader>.*)_(GEO)",
        title="Validation regex",
        description=(
            "Regex for validating name of top level group name. You can use"
            " named capturing groups:(?P<asset>.*) for Asset name"
        )
    )
    top_level_regex: str = Field(
        ".*_GRP",
        title="Top level group name regex",
        description=(
            "To check for asset in name so *_some_asset_name_GRP"
            " is valid, use:.*?_(?P<asset>.*)_GEO"
        )
    )


class ValidateModelContentModel(BaseSettingsModel):
    enabled: bool = Field(title="Enabled")
    optional: bool = Field(title="Optional")
    validate_top_group: bool = Field(title="Validate one top group")


class ValidateTransformNamingSuffixModel(BaseSettingsModel):
    enabled: bool = Field(title="Enabled")
    optional: bool = Field(title="Optional")
    SUFFIX_NAMING_TABLE: str = Field(
        "{}",
        title="Suffix Naming Tables",
        widget="textarea",
        description=(
            "Validates transform suffix based on"
            " the type of its children shapes."
        )
    )

    @validator("SUFFIX_NAMING_TABLE")
    def validate_json(cls, value):
        if not value.strip():
            return "{}"
        try:
            converted_value = json.loads(value)
            success = isinstance(converted_value, dict)
        except json.JSONDecodeError:
            success = False

        if not success:
            raise BadRequestException(
                "The text can't be parsed as json object"
            )
        return value
    ALLOW_IF_NOT_IN_SUFFIX_TABLE: bool = Field(
        title="Allow if suffix not in table"
    )


class CollectMayaRenderModel(BaseSettingsModel):
    sync_workfile_version: bool = Field(
        title="Sync render version with workfile"
    )


class CollectFbxAnimationModel(BaseSettingsModel):
    enabled: bool = Field(title="Collect Fbx Animation")


class CollectFbxCameraModel(BaseSettingsModel):
    enabled: bool = Field(title="CollectFbxCamera")


class CollectGLTFModel(BaseSettingsModel):
    enabled: bool = Field(title="CollectGLTF")


class ValidateFrameRangeModel(BaseSettingsModel):
    enabled: bool = Field(title="ValidateFrameRange")
    optional: bool = Field(title="Optional")
    active: bool = Field(title="Active")
    exclude_product_types: list[str] = Field(
        default_factory=list,
        title="Exclude product types"
    )


class ValidateShaderNameModel(BaseSettingsModel):
    """
    Shader name regex can use named capture group asset to validate against current asset name.
    """
    enabled: bool = Field(title="ValidateShaderName")
    optional: bool = Field(title="Optional")
    active: bool = Field(title="Active")
    regex: str = Field("(?P<asset>.*)_(.*)_SHD", title="Validation regex")


class ValidateAttributesModel(BaseSettingsModel):
    enabled: bool = Field(title="ValidateAttributes")
    attributes: str = Field(
        "{}", title="Attributes", widget="textarea")

    @validator("attributes")
    def validate_json(cls, value):
        if not value.strip():
            return "{}"
        try:
            converted_value = json.loads(value)
            success = isinstance(converted_value, dict)
        except json.JSONDecodeError:
            success = False

        if not success:
            raise BadRequestException(
                "The attibutes can't be parsed as json object"
            )
        return value


class ValidateLoadedPluginModel(BaseSettingsModel):
    enabled: bool = Field(title="ValidateLoadedPlugin")
    optional: bool = Field(title="Optional")
    whitelist_native_plugins: bool = Field(
        title="Whitelist Maya Native Plugins"
    )
    authorized_plugins: list[str] = Field(
        default_factory=list, title="Authorized plugins"
    )


class ValidateMayaUnitsModel(BaseSettingsModel):
    enabled: bool = Field(title="ValidateMayaUnits")
    optional: bool = Field(title="Optional")
    validate_linear_units: bool = Field(title="Validate linear units")
    linear_units: str = Field(
        enum_resolver=linear_unit_enum, title="Linear Units"
    )
    validate_angular_units: bool = Field(title="Validate angular units")
    angular_units: str = Field(
        enum_resolver=angular_unit_enum, title="Angular units"
    )
    validate_fps: bool = Field(title="Validate fps")


class ValidateUnrealStaticMeshNameModel(BaseSettingsModel):
    enabled: bool = Field(title="ValidateUnrealStaticMeshName")
    optional: bool = Field(title="Optional")
    validate_mesh: bool = Field(title="Validate mesh names")
    validate_collision: bool = Field(title="Validate collison names")


class ValidateCycleErrorModel(BaseSettingsModel):
    enabled: bool = Field(title="ValidateCycleError")
    optional: bool = Field(title="Optional")
    families: list[str] = Field(default_factory=list, title="Families")


class ValidatePluginPathAttributesAttrModel(BaseSettingsModel):
    name: str = Field(title="Node type")
    value: str = Field(title="Attribute")


class ValidatePluginPathAttributesModel(BaseSettingsModel):
    """Fill in the node types and attributes you want to validate.

    <p>e.g. <b>AlembicNode.abc_file</b>, the node type is <b>AlembicNode</b>
    and the node attribute is <b>abc_file</b>
    """

    enabled: bool = True
    optional: bool = Field(title="Optional")
    active: bool = Field(title="Active")
    attribute: list[ValidatePluginPathAttributesAttrModel] = Field(
        default_factory=list,
        title="File Attribute"
    )

    @validator("attribute")
    def validate_unique_outputs(cls, value):
        ensure_unique_names(value)
        return value


# Validate Render Setting
class RendererAttributesModel(BaseSettingsModel):
    _layout = "compact"
    type: str = Field(title="Type")
    value: str = Field(title="Value")


class ValidateRenderSettingsModel(BaseSettingsModel):
    arnold_render_attributes: list[RendererAttributesModel] = Field(
        default_factory=list, title="Arnold Render Attributes")
    vray_render_attributes: list[RendererAttributesModel] = Field(
        default_factory=list, title="VRay Render Attributes")
    redshift_render_attributes: list[RendererAttributesModel] = Field(
        default_factory=list, title="Redshift Render Attributes")
    renderman_render_attributes: list[RendererAttributesModel] = Field(
        default_factory=list, title="Renderman Render Attributes")


class BasicValidateModel(BaseSettingsModel):
    enabled: bool = Field(title="Enabled")
    optional: bool = Field(title="Optional")
    active: bool = Field(title="Active")


class ValidateCameraContentsModel(BaseSettingsModel):
    enabled: bool = Field(title="Enabled")
    optional: bool = Field(title="Optional")
    validate_shapes: bool = Field(title="Validate presence of shapes")


class ExtractProxyAlembicModel(BaseSettingsModel):
    enabled: bool = Field(title="Enabled")
    families: list[str] = Field(
        default_factory=list,
        title="Families")


class ExtractAlembicModel(BaseSettingsModel):
    enabled: bool = Field(title="Enabled")
    families: list[str] = Field(
        default_factory=list,
        title="Families")


class ExtractObjModel(BaseSettingsModel):
    enabled: bool = Field(title="Enabled")
    optional: bool = Field(title="Optional")


class ExtractMayaSceneRawModel(BaseSettingsModel):
    """Add loaded instances to those published families:"""
    enabled: bool = Field(title="ExtractMayaSceneRaw")
    add_for_families: list[str] = Field(default_factory=list, title="Families")


class ExtractCameraAlembicModel(BaseSettingsModel):
    """
    List of attributes that will be added to the baked alembic camera. Needs to be written in python list syntax.
    """
    enabled: bool = Field(title="ExtractCameraAlembic")
    optional: bool = Field(title="Optional")
    active: bool = Field(title="Active")
    bake_attributes: str = Field(
        "[]", title="Base Attributes", widget="textarea"
    )

    @validator("bake_attributes")
    def validate_json_list(cls, value):
        if not value.strip():
            return "[]"
        try:
            converted_value = json.loads(value)
            success = isinstance(converted_value, list)
        except json.JSONDecodeError:
            success = False

        if not success:
            raise BadRequestException(
                "The text can't be parsed as json object"
            )
        return value


class ExtractGLBModel(BaseSettingsModel):
    enabled: bool = True
    active: bool = Field(title="Active")
    ogsfx_path: str = Field(title="GLSL Shader Directory")


class ExtractLookArgsModel(BaseSettingsModel):
    argument: str = Field(title="Argument")
    parameters: list[str] = Field(default_factory=list, title="Parameters")


class ExtractLookModel(BaseSettingsModel):
    maketx_arguments: list[ExtractLookArgsModel] = Field(
        default_factory=list,
        title="Extra arguments for maketx command line"
    )


class ExtractGPUCacheModel(BaseSettingsModel):
    enabled: bool = True
    families: list[str] = Field(default_factory=list, title="Families")
    step: float = Field(1.0, ge=1.0, title="Step")
    stepSave: int = Field(1, ge=1, title="Step Save")
    optimize: bool = Field(title="Optimize Hierarchy")
    optimizationThreshold: int = Field(1, ge=1, title="Optimization Threshold")
    optimizeAnimationsForMotionBlur: bool = Field(
        title="Optimize Animations For Motion Blur"
    )
    writeMaterials: bool = Field(title="Write Materials")
    useBaseTessellation: bool = Field(title="User Base Tesselation")


class PublishersModel(BaseSettingsModel):
    CollectMayaRender: CollectMayaRenderModel = Field(
        default_factory=CollectMayaRenderModel,
        title="Collect Render Layers",
        section="Collectors"
    )
    CollectFbxAnimation: CollectFbxAnimationModel = Field(
        default_factory=CollectFbxAnimationModel,
        title="Collect FBX Animation",
    )
    CollectFbxCamera: CollectFbxCameraModel = Field(
        default_factory=CollectFbxCameraModel,
        title="Collect Camera for FBX export",
    )
    CollectGLTF: CollectGLTFModel = Field(
        default_factory=CollectGLTFModel,
        title="Collect Assets for GLB/GLTF export"
    )
    ValidateInstanceInContext: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Instance In Context",
        section="Validators"
    )
    ValidateContainers: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Containers"
    )
    ValidateFrameRange: ValidateFrameRangeModel = Field(
        default_factory=ValidateFrameRangeModel,
        title="Validate Frame Range"
    )
    ValidateShaderName: ValidateShaderNameModel = Field(
        default_factory=ValidateShaderNameModel,
        title="Validate Shader Name"
    )
    ValidateShadingEngine: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Look Shading Engine Naming"
    )
    ValidateMayaColorSpace: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Colorspace"
    )
    ValidateAttributes: ValidateAttributesModel = Field(
        default_factory=ValidateAttributesModel,
        title="Validate Attributes"
    )
    ValidateLoadedPlugin: ValidateLoadedPluginModel = Field(
        default_factory=ValidateLoadedPluginModel,
        title="Validate Loaded Plugin"
    )
    ValidateMayaUnits: ValidateMayaUnitsModel = Field(
        default_factory=ValidateMayaUnitsModel,
        title="Validate Maya Units"
    )
    ValidateUnrealStaticMeshName: ValidateUnrealStaticMeshNameModel = Field(
        default_factory=ValidateUnrealStaticMeshNameModel,
        title="Validate Unreal Static Mesh Name"
    )
    ValidateCycleError: ValidateCycleErrorModel = Field(
        default_factory=ValidateCycleErrorModel,
        title="Validate Cycle Error"
    )
    ValidatePluginPathAttributes: ValidatePluginPathAttributesModel = Field(
        default_factory=ValidatePluginPathAttributesModel,
        title="Plug-in Path Attributes"
    )
    ValidateRenderSettings: ValidateRenderSettingsModel = Field(
        default_factory=ValidateRenderSettingsModel,
        title="Validate Render Settings"
    )
    ValidateResolution: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Resolution Setting"
    )
    ValidateCurrentRenderLayerIsRenderable: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Current Render Layer Has Renderable Camera"
    )
    ValidateGLSLMaterial: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate GLSL Material"
    )
    ValidateGLSLPlugin: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate GLSL Plugin"
    )
    ValidateRenderImageRule: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Render Image Rule (Workspace)"
    )
    ValidateRenderNoDefaultCameras: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate No Default Cameras Renderable"
    )
    ValidateRenderSingleCamera: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Render Single Camera "
    )
    ValidateRenderLayerAOVs: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Render Passes/AOVs Are Registered"
    )
    ValidateStepSize: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Step Size"
    )
    ValidateVRayDistributedRendering: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="VRay Distributed Rendering"
    )
    ValidateVrayReferencedAOVs: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="VRay Referenced AOVs"
    )
    ValidateVRayTranslatorEnabled: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="VRay Translator Settings"
    )
    ValidateVrayProxy: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="VRay Proxy Settings"
    )
    ValidateVrayProxyMembers: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="VRay Proxy Members"
    )
    ValidateYetiRenderScriptCallbacks: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Yeti Render Script Callbacks"
    )
    ValidateYetiRigCacheState: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Yeti Rig Cache State"
    )
    ValidateYetiRigInputShapesInInstance: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Yeti Rig Input Shapes In Instance"
    )
    ValidateYetiRigSettings: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Yeti Rig Settings"
    )
    # Model - START
    ValidateModelName: ValidateModelNameModel = Field(
        default_factory=ValidateModelNameModel,
        title="Validate Model Name",
        section="Model",
    )
    ValidateModelContent: ValidateModelContentModel = Field(
        default_factory=ValidateModelContentModel,
        title="Validate Model Content",
    )
    ValidateTransformNamingSuffix: ValidateTransformNamingSuffixModel = Field(
        default_factory=ValidateTransformNamingSuffixModel,
        title="Validate Transform Naming Suffix",
    )
    ValidateColorSets: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Color Sets",
    )
    ValidateMeshHasOverlappingUVs: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Mesh Has Overlapping UVs",
    )
    ValidateMeshArnoldAttributes: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Mesh Arnold Attributes",
    )
    ValidateMeshShaderConnections: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Mesh Shader Connections",
    )
    ValidateMeshSingleUVSet: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Mesh Single UV Set",
    )
    ValidateMeshHasUVs: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Mesh Has UVs",
    )
    ValidateMeshLaminaFaces: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Mesh Lamina Faces",
    )
    ValidateMeshNgons: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Mesh Ngons",
    )
    ValidateMeshNonManifold: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Mesh Non-Manifold",
    )
    ValidateMeshNoNegativeScale: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Mesh No Negative Scale",
    )
    ValidateMeshNonZeroEdgeLength: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Mesh Edge Length Non Zero",
    )
    ValidateMeshNormalsUnlocked: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Mesh Normals Unlocked",
    )
    ValidateMeshUVSetMap1: ValidateMeshUVSetMap1Model = Field(
        default_factory=ValidateMeshUVSetMap1Model,
        title="Validate Mesh UV Set Map 1",
    )
    ValidateMeshVerticesHaveEdges: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Mesh Vertices Have Edges",
    )
    ValidateNoAnimation: ValidateNoAnimationModel = Field(
        default_factory=ValidateNoAnimationModel,
        title="Validate No Animation",
    )
    ValidateNoNamespace: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate No Namespace",
    )
    ValidateNoNullTransforms: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate No Null Transforms",
    )
    ValidateNoUnknownNodes: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate No Unknown Nodes",
    )
    ValidateNodeNoGhosting: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Node No Ghosting",
    )
    ValidateShapeDefaultNames: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Shape Default Names",
    )
    ValidateShapeRenderStats: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Shape Render Stats",
    )
    ValidateShapeZero: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Shape Zero",
    )
    ValidateTransformZero: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Transform Zero",
    )
    ValidateUniqueNames: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Unique Names",
    )
    ValidateNoVRayMesh: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate No V-Ray Proxies (VRayMesh)",
    )
    ValidateUnrealMeshTriangulated: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate if Mesh is Triangulated",
    )
    ValidateAlembicVisibleOnly: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Alembic Visible Node",
    )
    ExtractProxyAlembic: ExtractProxyAlembicModel = Field(
        default_factory=ExtractProxyAlembicModel,
        title="Extract Proxy Alembic",
        section="Model Extractors",
    )
    ExtractAlembic: ExtractAlembicModel = Field(
        default_factory=ExtractAlembicModel,
        title="Extract Alembic",
    )
    ExtractObj: ExtractObjModel = Field(
        default_factory=ExtractObjModel,
        title="Extract OBJ"
    )
    # Model - END

    # Rig - START
    ValidateRigContents: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Rig Contents",
        section="Rig",
    )
    ValidateRigJointsHidden: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Rig Joints Hidden",
    )
    ValidateRigControllers: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Rig Controllers",
    )
    ValidateAnimatedReferenceRig: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Animated Reference Rig",
    )
    ValidateAnimationContent: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Animation Content",
    )
    ValidateOutRelatedNodeIds: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Animation Out Set Related Node Ids",
    )
    ValidateRigControllersArnoldAttributes: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Rig Controllers (Arnold Attributes)",
    )
    ValidateSkeletalMeshHierarchy: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Skeletal Mesh Top Node",
    )
    ValidateSkeletonRigContents: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Skeleton Rig Contents"
    )
    ValidateSkeletonRigControllers: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Skeleton Rig Controllers"
    )
    ValidateSkinclusterDeformerSet: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Skincluster Deformer Relationships",
    )
    ValidateSkeletonRigOutputIds: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Skeleton Rig Output Ids"
    )
    ValidateSkeletonTopGroupHierarchy: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Skeleton Top Group Hierarchy",
    )
    ValidateRigOutSetNodeIds: ValidateRigOutSetNodeIdsModel = Field(
        default_factory=ValidateRigOutSetNodeIdsModel,
        title="Validate Rig Out Set Node Ids",
    )
    ValidateSkeletonRigOutSetNodeIds: ValidateRigOutSetNodeIdsModel = Field(
        default_factory=ValidateRigOutSetNodeIdsModel,
        title="Validate Skeleton Rig Out Set Node Ids",
    )
    # Rig - END
    ValidateCameraAttributes: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Camera Attributes"
    )
    ValidateAssemblyName: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Assembly Name"
    )
    ValidateAssemblyNamespaces: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Assembly Namespaces"
    )
    ValidateAssemblyModelTransforms: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Assembly Model Transforms"
    )
    ValidateAssRelativePaths: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Ass Relative Paths"
    )
    ValidateInstancerContent: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Instancer Content"
    )
    ValidateInstancerFrameRanges: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Instancer Cache Frame Ranges"
    )
    ValidateNoDefaultCameras: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate No Default Cameras"
    )
    ValidateUnrealUpAxis: BasicValidateModel = Field(
        default_factory=BasicValidateModel,
        title="Validate Unreal Up-Axis Check"
    )
    ValidateCameraContents: ValidateCameraContentsModel = Field(
        default_factory=ValidateCameraContentsModel,
        title="Validate Camera Content"
    )
    ExtractPlayblast: ExtractPlayblastSetting = Field(
        default_factory=ExtractPlayblastSetting,
        title="Extract Playblast Settings",
        section="Extractors"
    )
    ExtractMayaSceneRaw: ExtractMayaSceneRawModel = Field(
        default_factory=ExtractMayaSceneRawModel,
        title="Maya Scene(Raw)"
    )
    ExtractCameraAlembic: ExtractCameraAlembicModel = Field(
        default_factory=ExtractCameraAlembicModel,
        title="Extract Camera Alembic"
    )
    ExtractGLB: ExtractGLBModel = Field(
        default_factory=ExtractGLBModel,
        title="Extract GLB"
    )
    ExtractLook: ExtractLookModel = Field(
        default_factory=ExtractLookModel,
        title="Extract Look"
    )
    ExtractGPUCache: ExtractGPUCacheModel = Field(
        default_factory=ExtractGPUCacheModel,
        title="Extract GPU Cache",
    )


DEFAULT_SUFFIX_NAMING = {
    "mesh": ["_GEO", "_GES", "_GEP", "_OSD"],
    "nurbsCurve": ["_CRV"],
    "nurbsSurface": ["_NRB"],
    "locator": ["_LOC"],
    "group": ["_GRP"]
}

DEFAULT_PUBLISH_SETTINGS = {
    "CollectMayaRender": {
        "sync_workfile_version": False
    },
    "CollectFbxAnimation": {
        "enabled": False
    },
    "CollectFbxCamera": {
        "enabled": False
    },
    "CollectGLTF": {
        "enabled": False
    },
    "ValidateInstanceInContext": {
        "enabled": True,
        "optional": True,
        "active": True
    },
    "ValidateContainers": {
        "enabled": True,
        "optional": True,
        "active": True
    },
    "ValidateFrameRange": {
        "enabled": True,
        "optional": True,
        "active": True,
        "exclude_product_types": [
            "model",
            "rig",
            "staticMesh"
        ]
    },
    "ValidateShaderName": {
        "enabled": False,
        "optional": True,
        "active": True,
        "regex": "(?P<asset>.*)_(.*)_SHD"
    },
    "ValidateShadingEngine": {
        "enabled": True,
        "optional": True,
        "active": True
    },
    "ValidateMayaColorSpace": {
        "enabled": True,
        "optional": True,
        "active": True
    },
    "ValidateAttributes": {
        "enabled": False,
        "attributes": "{}"
    },
    "ValidateLoadedPlugin": {
        "enabled": False,
        "optional": True,
        "whitelist_native_plugins": False,
        "authorized_plugins": []
    },
    "ValidateMayaUnits": {
        "enabled": True,
        "optional": False,
        "validate_linear_units": True,
        "linear_units": "cm",
        "validate_angular_units": True,
        "angular_units": "deg",
        "validate_fps": True
    },
    "ValidateUnrealStaticMeshName": {
        "enabled": True,
        "optional": True,
        "validate_mesh": False,
        "validate_collision": True
    },
    "ValidateCycleError": {
        "enabled": True,
        "optional": False,
        "families": [
            "rig"
        ]
    },
    "ValidatePluginPathAttributes": {
        "enabled": False,
        "optional": False,
        "active": True,
        "attribute": [
            {"name": "AlembicNode", "value": "abc_File"},
            {"name": "VRayProxy", "value": "fileName"},
            {"name": "RenderManArchive", "value": "filename"},
            {"name": "pgYetiMaya", "value": "cacheFileName"},
            {"name": "aiStandIn", "value": "dso"},
            {"name": "RedshiftSprite", "value": "tex0"},
            {"name": "RedshiftBokeh", "value": "dofBokehImage"},
            {"name": "RedshiftCameraMap", "value": "tex0"},
            {"name": "RedshiftEnvironment", "value": "tex2"},
            {"name": "RedshiftDomeLight", "value": "tex1"},
            {"name": "RedshiftIESLight", "value": "profile"},
            {"name": "RedshiftLightGobo", "value": "tex0"},
            {"name": "RedshiftNormalMap", "value": "tex0"},
            {"name": "RedshiftProxyMesh", "value": "fileName"},
            {"name": "RedshiftVolumeShape", "value": "fileName"},
            {"name": "VRayTexGLSL", "value": "fileName"},
            {"name": "VRayMtlGLSL", "value": "fileName"},
            {"name": "VRayVRmatMtl", "value": "fileName"},
            {"name": "VRayPtex", "value": "ptexFile"},
            {"name": "VRayLightIESShape", "value": "iesFile"},
            {"name": "VRayMesh", "value": "materialAssignmentsFile"},
            {"name": "VRayMtlOSL", "value": "fileName"},
            {"name": "VRayTexOSL", "value": "fileName"},
            {"name": "VRayTexOCIO", "value": "ocioConfigFile"},
            {"name": "VRaySettingsNode", "value": "pmap_autoSaveFile2"},
            {"name": "VRayScannedMtl", "value": "file"},
            {"name": "VRayScene", "value": "parameterOverrideFilePath"},
            {"name": "VRayMtlMDL", "value": "filename"},
            {"name": "VRaySimbiont", "value": "file"},
            {"name": "dlOpenVDBShape", "value": "filename"},
            {"name": "pgYetiMayaShape", "value": "liveABCFilename"},
            {"name": "gpuCache", "value": "cacheFileName"},
        ]
    },
    "ValidateRenderSettings": {
        "arnold_render_attributes": [],
        "vray_render_attributes": [],
        "redshift_render_attributes": [],
        "renderman_render_attributes": []
    },
    "ValidateResolution": {
        "enabled": True,
        "optional": True,
        "active": True
    },
    "ValidateCurrentRenderLayerIsRenderable": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateGLSLMaterial": {
        "enabled": False,
        "optional": False,
        "active": True
    },
    "ValidateGLSLPlugin": {
        "enabled": False,
        "optional": False,
        "active": True
    },
    "ValidateRenderImageRule": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateRenderNoDefaultCameras": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateRenderSingleCamera": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateRenderLayerAOVs": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateStepSize": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateVRayDistributedRendering": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateVrayReferencedAOVs": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateVRayTranslatorEnabled": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateVrayProxy": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateVrayProxyMembers": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateYetiRenderScriptCallbacks": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateYetiRigCacheState": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateYetiRigInputShapesInInstance": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateYetiRigSettings": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateModelName": {
        "enabled": False,
        "database": True,
        "material_file": {
            "windows": "",
            "darwin": "",
            "linux": ""
        },
        "regex": "(.*)_(\\d)*_(?P<shader>.*)_(GEO)",
        "top_level_regex": ".*_GRP"
    },
    "ValidateModelContent": {
        "enabled": True,
        "optional": False,
        "validate_top_group": True
    },
    "ValidateTransformNamingSuffix": {
        "enabled": True,
        "optional": True,
        "SUFFIX_NAMING_TABLE": json.dumps(DEFAULT_SUFFIX_NAMING, indent=4),
        "ALLOW_IF_NOT_IN_SUFFIX_TABLE": True
    },
    "ValidateColorSets": {
        "enabled": True,
        "optional": True,
        "active": True
    },
    "ValidateMeshHasOverlappingUVs": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateMeshArnoldAttributes": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateMeshShaderConnections": {
        "enabled": True,
        "optional": True,
        "active": True
    },
    "ValidateMeshSingleUVSet": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateMeshHasUVs": {
        "enabled": True,
        "optional": True,
        "active": True
    },
    "ValidateMeshLaminaFaces": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateMeshNgons": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateMeshNonManifold": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateMeshNoNegativeScale": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateMeshNonZeroEdgeLength": {
        "enabled": True,
        "optional": True,
        "active": True
    },
    "ValidateMeshNormalsUnlocked": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateMeshUVSetMap1": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateMeshVerticesHaveEdges": {
        "enabled": True,
        "optional": True,
        "active": True
    },
    "ValidateNoAnimation": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateNoNamespace": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateNoNullTransforms": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateNoUnknownNodes": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateNodeNoGhosting": {
        "enabled": False,
        "optional": False,
        "active": True
    },
    "ValidateShapeDefaultNames": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateShapeRenderStats": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateShapeZero": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateTransformZero": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateUniqueNames": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateNoVRayMesh": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateUnrealMeshTriangulated": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateAlembicVisibleOnly": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ExtractProxyAlembic": {
        "enabled": False,
        "families": [
            "proxyAbc"
        ]
    },
    "ExtractAlembic": {
        "enabled": True,
        "families": [
            "pointcache",
            "model",
            "vrayproxy.alembic"
        ]
    },
    "ExtractObj": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateRigContents": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateRigJointsHidden": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateRigControllers": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateAnimatedReferenceRig": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateAnimationContent": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateOutRelatedNodeIds": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateRigControllersArnoldAttributes": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateSkeletalMeshHierarchy": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateSkeletonRigContents": {
        "enabled": True,
        "optional": True,
        "active": True
    },
    "ValidateSkeletonRigControllers": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateSkinclusterDeformerSet": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateRigOutSetNodeIds": {
        "enabled": True,
        "optional": False,
        "allow_history_only": False
    },
    "ValidateSkeletonRigOutSetNodeIds": {
        "enabled": False,
        "optional": False,
        "allow_history_only": False
    },
    "ValidateSkeletonRigOutputIds": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateSkeletonTopGroupHierarchy": {
        "enabled": True,
        "optional": True,
        "active": True
    },
    "ValidateCameraAttributes": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateAssemblyName": {
        "enabled": True,
        "optional": True,
        "active": True
    },
    "ValidateAssemblyNamespaces": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateAssemblyModelTransforms": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateAssRelativePaths": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateInstancerContent": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateInstancerFrameRanges": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateNoDefaultCameras": {
        "enabled": True,
        "optional": False,
        "active": True
    },
    "ValidateUnrealUpAxis": {
        "enabled": False,
        "optional": True,
        "active": True
    },
    "ValidateCameraContents": {
        "enabled": True,
        "optional": False,
        "validate_shapes": True
    },
    "ExtractPlayblast": DEFAULT_PLAYBLAST_SETTING,
    "ExtractMayaSceneRaw": {
        "enabled": True,
        "add_for_families": [
            "layout"
        ]
    },
    "ExtractCameraAlembic": {
        "enabled": True,
        "optional": True,
        "active": True,
        "bake_attributes": "[]"
    },
    "ExtractGLB": {
        "enabled": False,
        "active": True,
        "ogsfx_path": "/maya2glTF/PBR/shaders/glTF_PBR.ogsfx"
    },
    "ExtractLook": {
        "maketx_arguments": []
    },
    "ExtractGPUCache": {
        "enabled": False,
        "families": [
            "model",
            "animation",
            "pointcache"
        ],
        "step": 1.0,
        "stepSave": 1,
        "optimize": True,
        "optimizationThreshold": 40000,
        "optimizeAnimationsForMotionBlur": True,
        "writeMaterials": True,
        "useBaseTessellation": True
    }
}
