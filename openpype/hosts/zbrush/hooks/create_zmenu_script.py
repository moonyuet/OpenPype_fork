"""Pre-launch to force zbrush startup script."""
import os
from openpype.hosts.zbrush import ZBRUSH_HOST_DIR
from openpype import AYON_SERVER_ENABLED
from openpype.lib.applications import PreLaunchHook, LaunchTypes



class CreateZMenuScript(PreLaunchHook):
    """Create AYON Menu Zscript to Zbrush.

    Note that this works in combination whit Zbrush startup script
    to successfully install zscripts.menu

    Hook `GlobalHostDataHook` must be executed before this hook.
    """
    app_groups = {"zbrush"}
    order = 10
    launch_types = {LaunchTypes.local}

    def execute(self):
        zscript_path = os.path.join(ZBRUSH_HOST_DIR, "api", "zscripts")
        zscript_txt = os.path.join(zscript_path, "ayon_zbrush_menu.txt")
        with open(zscript_txt, "w") as zscript:
            zscript.write(self.ayon_menu())
            zscript.close()

    def ayon_menu(self):
        zclient_path = os.path.join(ZBRUSH_HOST_DIR, "api", "widgets.py")
        zclient_path = zclient_path.replace("\\", "/")
        python_exe = (
            os.environ["AYON_EXECUTABLE"] if AYON_SERVER_ENABLED
            else os.environ["OPENPYPE_EXECUTABLE"]
        )
        ayon_script = ("""

[RoutineDef, CheckSystem,
    //check ZBrush version
    [VarSet, Zvers, [ZBrushInfo,0]]
    [If, [Val, Zvers] >= 4.8,,
        [Note,"\Cff9923This zscript\Cffffff is not designed for this version of \Cff9923ZBrush\Cffffff.",, 3, 4737096,, 300]
        [Exit]
    ]
    //check Mac or PC
    [VarSet, isMac, [ZBrushInfo, 6]]

    // Make sure we have the dll and set its path
    [If, [ZBrushInfo, 16] == 64,//64 bit
        [If, isMac,
            [VarSet,dllPath,[FileNameResolvePath, "ZFileUtils.lib"]]
        ,
            [VarSet,dllPath,[FileNameResolvePath, "ZFileUtils64.dll"]]
        ]
    , //else 32 bit - no longer supported
        [Note, "\Cff9923This zscript\Cffffff is not designed for this version of \Cff9923ZBrush\Cffffff.",, 3, 4737096,, 300]
        [Exit]
    ]
    [If, [FileExists, [Var, dllPath]],
        //check that correct version
        [VarSet, dllVersion, [FileExecute, [Var, dllPath], Version]]
        [If, [Val,dllVersion] >= 3.0,//dll version
            //OK
        ,//else earlier version
            [Note,"\Cff9923Note :\Cc0c0c0 The \Cff9923 ZFileUtils plugin \CffffffDLL\Cc0c0c0 is an earlier version which does not support this plugin.  Please install correct version."]
            [Exit]
        ]
    , // else no DLL.
        [Note,"\Cff9923Note :\Cc0c0c0 The \Cff9923 ZFileUtils plugin \CffffffDLL\Cc0c0c0 could
        not be found at the correct location.  Please re-install the plugin, making sure the
        relevant files and folders are in the \CffffffZStartup/ZPlugs\Cc0c0c0 folder."]
        [Exit]
    ]
    // set dll path in memory block
    [If, [MemGetSize, zlmMFileUtilPath],
        [MemResize, zlmMFileUtilPath, [StrLength, dllPath]]
    ,
        [MemCreate, zlmMFileUtilPath, [StrLength, dllPath]]
    ]
    [VarSet, size, [MemWriteString, zlmMFileUtilPath, #dllPath,0,0]]
    [MemResize, zlmMFileUtilPath, size]

]//end routine

[RoutineCall, CheckSystem]
[VarDef,dllPath,""]//path to dll
[VarDef,err,0]//standard error
[VarDef,ver,0]//version
[VarDef,stringArg,""]
[VarDef,responseString,""]

[RoutineDef,CheckSystem,
	[VarSet,dllPath,"ZSOCKET.dll"]
	[If,[FileExists,dllPath],
		,
		[Note,"DLL is missing"][Exit]
	]
]
[ISubPalette,"Zplugin:AYON"]
[IButton,"Zplugin:AYON:Load","Loader",
	[VarSet,sc, "{client_script}"]
	[VarSet, loader, "loader_tool"]
    [VarSet, q, [StrFromAsc, 34]]
	[VarSet, cmd, [StrMerge, start, " ",#q, #q, "  ",#q, "{py}",#q, " ",#q, sc, #q]]
	[VarSet, cmd, [StrMerge, cmd, " ", #loader, #q]]
	[ShellExecute, cmd], 0, 120
]//end button
[IButton,"Zplugin:AYON:Publish","Publish Tab for Publisher",
	[VarSet, sc, "{client_script}"]
	[VarSet, publisher, "publish_tool"]
    [VarSet, q, [StrFromAsc, 34]]
	[VarSet, cmd, [StrMerge, start, " ",#q, #q, "  ",#q, "{py}",#q, " ",#q, sc, #q]]
	[VarSet, cmd, [StrMerge, cmd, " ", #publisher, #q]]
	[ShellExecute, cmd], 0, 120
]//end button
[IButton,"Zplugin:AYON:Manage","Scene Inventory Manager",
	[VarSet, sc, "{client_script}"]
	[VarSet, sceneinventory, "scene_inventory_tool"]
    [VarSet, q, [StrFromAsc, 34]]
	[VarSet, cmd, [StrMerge, start, " ",#q, #q, "  ",#q, "{py}",#q, " ",#q, sc, #q]]
	[VarSet, cmd, [StrMerge, cmd, " ", #sceneinventory, #q]]
	[ShellExecute, cmd], 0, 120
]//end button
[IButton,"Zplugin:AYON:Workfile","Workfile",
	[VarSet,sc, "{client_script}"]
	[VarSet, workfiles, "workfiles_tool"]
	    [VarSet, q, [StrFromAsc, 34]]
	[VarSet, cmd, [StrMerge, start, " ",#q, #q, "  ",#q, "{py}",#q, " ",#q, sc, #q]]
	[VarSet, cmd, [StrMerge, cmd, " ", #workfiles, #q]]
	[ShellExecute, cmd], 0, 120
]//end button""").format(client_script=zclient_path, py=python_exe)
        return ayon_script
