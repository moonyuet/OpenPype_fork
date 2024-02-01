import os
import tempfile
from .lib import execute_zscript

def save_file(filepath):
    save_file_zscript = ("""
[MemCreate, currentfile, 100, 0]
[VarSet, filename, "{filepath}"]
[MemWriteString, currentfile, #filename, 0]
[FileNameSetNext, #filename]
[IKeyPress, 13, [IPress, File:Save:Save]]

""").format(filepath=filepath)
    execute_zscript(save_file_zscript)

def open_file(filepath):
    open_file_zscript = ("""
[MemCreate, currentfile, 100, 0]
[VarSet, filename, "{filepath}"]
[MemWriteString, currentfile, #filename, 0]
[FileNameSetNext, #filename]
[IKeyPress, 13, [IPress, File:Open:Open]]]

""").format(filepath=filepath)
    execute_zscript(open_file_zscript)

def get_current_filepath():
    output_file = tempfile.NamedTemporaryFile(
        mode="w", prefix="a_tvp_", suffix=".txt", delete=False
    )
    output_file.close()
    output_filepath = output_file.name.replace("\\", "/")
    find_current_filepath_zscript = ("""
[MemSaveToFile, currentfile, "{output_filepath}", 1]
[MemDelete, currentfile]

""").format(output_filepath=output_filepath)
    execute_zscript(find_current_filepath_zscript)
    if not os.path.exists(output_filepath):
        return None
    with open(output_filepath, "r") as current_file:
        return str(current_file.read())
