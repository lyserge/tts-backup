import json
import re
import os.path
import sys

from tts_tools.util import (
    ZipFile,
    print_err
)
from tts_tools.libtts import (
    urls_from_save,
    get_fs_path,
    IllegalSavegameException,
    WORKSHOPPATH
)


def restore_zip(args):
    #print(args.__dict__)

    if not os.path.isdir(args.gamedata_dir):
        errmsg = "Could not open gamedata directory '{dir}'".format(
            dir=args.gamedata_dir,
        )
        print_err(errmsg)
        sys.exit(1)

    workshop_filepath = os.path.join(args.gamedata_dir, WORKSHOPPATH, 'WorkshopFileInfos.json')
    if not os.path.isfile(workshop_filepath):
        errmsg = "Could not find Workshop info file at '{workshop_file}'".format(
            workshop_filepath=workshop_filepath,
        )
        print_err(errmsg)
        sys.exit(1)  

    try:
        zipfile = ZipFile(
            args.infile_name,
            'r',
            dry_run=args.dry_run,
            rewrite=args.rewrite
        )
    except FileNotFoundError as error:
        errmsg = "Could not find Zip archive '{infile_name}': {error}".format(
            infile_name=args.infile_name,
            error=error
        )
        print_err(errmsg)
        sys.exit(1)

    with zipfile as infile:
        print(zipfile.__dict__)
        infolist = infile.infolist()
        metadata = zipfile.get_metadata()

        try:
            infofile = metadata['info_filename']
            print(f'Found info file in metadata')
            info = infile.read(infofile)
        except KeyError:
            if infolist[-1].filename.endswith('.json'):
                infofile = infolist[-1].filename
                print(f'Found info file as last file')
            else:
                errmsg = "Could not find .json info file in '{infile_name}'".format(
                    infile_name=args.infile_name,
                )
                print_err(errmsg)
                sys.exit(1)
        finally:
            info = json.loads(infile.read(infofile))
            infofile_path = os.path.join(args.gamedata_dir, WORKSHOPPATH, infofile)

            if args.restore_name:
                restore_name = args.restore_name
                print(f"Extracting '{info['SaveName']}' as '{args.restore_name}'...")
            else:
                restore_name = info['SaveName']
                print(f"Extracting '{info['SaveName']}'...")

        for f in infile.infolist():
            try:
                if f.filename == infofile:
                    infile.extract(f, os.path.join(args.gamedata_dir, WORKSHOPPATH))
                else:
                    infile.extract(f, args.gamedata_dir)
            except Exception as error:
                errmsg = "Could not extract file '{outfile}': {error}".format(
                    outfile=os.path.join(args.gamedata_dir, f.filename),
                    error=error
                )
                print_err(errmsg)
                sys.exit(1)

    # TODO: update JSON
    if args.dry_run:
        mode = 'r'
    else:
        mode = 'r+'

    with open(workshop_filepath, mode, encoding='utf-8') as json_file:
        workshop_data = json.load(json_file)
        for index, item in enumerate(workshop_data):
            if (infofile_path == item['Directory'].replace('//', '/')) and (item['Name'] == restore_name):
                print(f"Item is already in the info")
                break
        else:
            item_info = {'Directory': infofile_path, 'Name': restore_name, 'UpdateTime': metadata['export_date']}
            if args.dry_run:
                print(f"Item would be added to your workshops info: { json.dumps(item_info) }")
            else:
                workshop_data.append(item_info)
                json_file.seek(0)
                json.dump(workshop_data, json_file, indent=2, ensure_ascii=False)
                print("Item added to your workshops info")

    

    if args.dry_run:
        print("Dry run for {file} completed.".format(file=args.infile_name))
    else:
        print("Restored contents from {infile_name} to {dir}.".format(
            infile_name=args.infile_name,
            dir=args.gamedata_dir
        ))
