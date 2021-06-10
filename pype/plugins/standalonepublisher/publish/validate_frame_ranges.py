import pyblish.api
import pype.api
from pype import lib


class ValidateFrameRange(pyblish.api.InstancePlugin):
    """Validating frame range of rendered files against state in DB."""

    label = "Validate Frame Range"
    hosts = ["standalonepublisher"]
    families = ["render"]
    order = pype.api.ValidateContentsOrder

    optional = True
    # published data might be sequence (.mov, .mp4) in that counting files
    # doesnt make sense
    check_extensions = ["exr", "dpx", "jpg", "jpeg", "png", "tiff", "tga",
                        "gif", "svg"]

    def process(self, instance):
        asset_data = lib.get_asset(instance.data["asset"])["data"]

        frame_start = asset_data["frameStart"]
        frame_end = asset_data["frameEnd"]
        handle_start = asset_data["handleStart"]
        handle_end = asset_data["handleEnd"]
        duration = (frame_end - frame_start + 1) + handle_start + handle_end

        repre = instance.data.get("representations", [None])
        if not repre:
            return

        ext = repre[0]['ext'].replace(".", '')

        if not ext or ext.lower() not in self.check_extensions:
            self.log.warning("Cannot check for extension {}".format(ext))
            return

        frames = len(instance.data.get("representations", [None])[0]["files"])

        err_msg = "Frame duration from DB:'{}' ". format(int(duration)) +\
                  " doesn't match number of files:'{}'".format(frames) +\
                  " Please change frame range for Asset or limit no. of files"
        assert frames == duration, err_msg
