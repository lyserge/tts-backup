import argparse

from tts_tools.libtts import GAMEDATA_DEFAULT
from tts_tools.restore import restore_zip


parser = argparse.ArgumentParser(
    description="Restore a TTS mod or save file to cache from a backup .zip."
)

parser.add_argument(
    'infile_name',
    metavar='FILENAME',
    help="The backup file in zip format."
)

parser.add_argument(
    "--gamedata",
    dest='gamedata_dir',
    metavar='PATH',
    default=GAMEDATA_DEFAULT,
    help="The path to the TTS game data dircetory."
)

parser.add_argument(
    "--restorename",
    dest='restore_name',
    metavar='RESTORENAME',
    default=None,
    help="The name to use for the mod inside TTS (if different from the one in the backup)."
)

parser.add_argument(
    "--rewrite", "-r",
    dest='rewrite',
    default=False,
    action='store_true',
    help="Rewrite objects that already exist in the cache."
)

parser.add_argument(
    "--dry-run", "-n",
    dest='dry_run',
    default=False,
    action='store_true',
    help="Only print which files would be restored."
)


def console_entry():

    args = parser.parse_args()
    restore_zip(args)
