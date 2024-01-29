import argparse
import logging
from openpype.hosts.zbrush.api.connection_script import open_widgets

log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="AYON Plugins")
    parser.add_argument('launchertype', type=str, help='Launcher Type')
    parser.add_argument('--update-zbrush', '-uz', action='store_true', help='update zbrush with layer from zlm. if opened')
    parser.add_argument('--update', '-u', action='store_true', help='Update zlm ui with zbrush layer if opened')
    args = parser.parse_args()

    if args.launchertype:
        open_widgets(launcher_type=args.launchertype)

    elif args.update:
        open_widgets.update_from_zbrush()

    elif args.update_zbrush:
        open_widgets.update_zbrush()

if __name__ == "__main__":
    main()
