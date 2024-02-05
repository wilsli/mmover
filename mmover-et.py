import os, argparse, exiftool, warnings
from pathlib import Path
from datetime import datetime
from shutil import copyfile, move
import time

__version__ = '0.9.e-beta'

parser = argparse.ArgumentParser(description="Filtering and handling media files in specific foler")

parser.add_argument("command", type=str, choices=['copy','move'], help="command to execute: \"copy\" or \"move\"")
parser.add_argument("media", type=str, choices=['image', 'video'], help="media type: \"image\" or \"video\"")
parser.add_argument("source_dir", type=Path, help="the path to the source folder which need to be scanned, e.g. \"/Path/to/the/source/folder\"")
parser.add_argument("target_dir", type=Path, help="the path to the target folder which pictures be copied/moved to, e.g. \"/Path/to/the/target/folder\"")
parser.add_argument("-r", "--recursive", action="store_true", help="scan the folders recursively")
parser.add_argument("-d", "--dryrun", action="store_true", help="dry run the command only")
parser.add_argument("-c", "--camera", metavar='MODEL', type=str, help='the model of the camera, e.g."iPhone XS"')
parser.add_argument("-b", "--before", metavar='YYYY-M-D', type=str, help='filter pictures taken before the given date yyyy-m-d 0:00 (excluded the date), e.g. "2000-1-1"')
parser.add_argument("-a", "--after", metavar='YYYY-M-D', type=str, help='filter pictures after the given date yyyy-m-d 0:00 (included the date), e.g."2000-1-1"')
# parser.add_argument("--rmcorrupt", action="store_true", help="delete corrupted picture files")
parser.add_argument("-v", "--version", action="version", version='MediaMover '+__version__)
args = parser.parse_args()
count = 0
idf_files = 0
hit_files = 0
exepath = "/Users/wilson/Envs/d-science/exiftool/exiftool"

if args.before:
    bdate = datetime.strptime(args.before, "%Y-%m-%d")

if args.after:
    adate = datetime.strptime(args.after, "%Y-%m-%d")
        
def check_type(metadata):
    if 'File:MIMEType' in metadata and metadata['File:MIMEType']:
        return metadata['File:MIMEType'].split('/')[0]
    else:
        return None

def get_create_date(metadata):
    date_mask = "%Y:%m:%d %H:%M:%S"
    if metadata:
        if 'EXIF:CreateDate' in metadata and metadata['EXIF:CreateDate']:
            d0 = datetime.strptime(metadata['EXIF:CreateDate'][:19], date_mask)
        else:
            d0 = datetime(9999,12,31,0,0,0)
        if 'QuickTime:CreateDate' in metadata and metadata['QuickTime:CreateDate']:
            d1 = datetime.strptime(metadata['QuickTime:CreateDate'][:19], date_mask)
        else:
            d1 = datetime(9999,12,31,0,0,0)
        if 'QuickTime:MediaCreateDate' in metadata and metadata['QuickTime:MediaCreateDate']:
            d2 = datetime.strptime(metadata['QuickTime:MediaCreateDate'][:19], date_mask)
        else:
            d2 = datetime(9999,12,31,0,0,0)
        if 'QuickTime:ContentCreateDate' in metadata and metadata['QuickTime:ContentCreateDate']:
            d3 = datetime.strptime(metadata['QuickTime:ContentCreateDate'][:19], date_mask)
        else:
            d3 = datetime(9999,12,31,0,0,0)
        date = min([d0,d1,d2,d3]) if min([d0,d1,d2,d3]) != datetime(9999,12,31,0,0,0) else None
        return date
    else:
        return None

def match_model(metadata, model):
    if ('EXIF:Model' in metadata and model in metadata['EXIF:Model']) or ('QuickTime:Model' in metadata and model in metadata['QuickTime:Model']):
        return True
    else:
        return False

def handle_file(src_dir, tgt_dir, filename):
    global idf_files, hit_files, args, adate, bdate, exepath
    src_file = os.path.join(src_dir, filename)
    tgt_file = os.path.join(tgt_dir, filename)

    with warnings.catch_warnings(record=True) as w:
        try:
            with exiftool.ExifToolHelper(executable=exepath) as et:
                meta = et.get_metadata(src_file, '-ee')
                if meta[0]:
                    _type = check_type(meta[0])
                    if args.media == _type:
                        if not args.camera or match_model(meta[0], args.camera):
                            date = get_create_date(meta[0])
                            if not (date and (args.before and date > bdate) or (args.after and date < adate)):
                                idf_files += 1
                                if args.command == "copy":
                                    if args.dryrun:
                                        print(f"[Dry run]Would copy: {src_file}")
                                    else:
                                        try:
                                            print(f"Copying: {src_file}")
                                            copyfile(src_file, tgt_file)
                                            hit_files += 1
                                        except Exception as copy_error:
                                            print(f"Failed to copy: {filename} due to {copy_error}")
                                elif args.command == "move":
                                    if args.dryrun:
                                        print(f"[Dry run]Would move: {src_file}")
                                    else:
                                        try:
                                            print(f"Moving: {src_file}")
                                            move(src_file, tgt_file)
                                            hit_files += 1
                                        except Exception as move_error:
                                            print(f"Failed to move {filename} due to {move_error}")
                else:
                    return
        except Exception as file_hdl_error:
            # if args.rmcorrupt and (isinstance(file_hdl_error, UnidentifiedImageError) or (isinstance(file_hdl_error, OSError) and file_hdl_error.args[0] == "Truncated File Read")):
            #     if args.dryrun:
            #         print(f"[Dry run]Would delete from source directory: {filename}")
            #     else:
            #         os.remove(src_file)
            #         print(f"Deleted [{filename}] from source directory: {file_hdl_error}")
            # else:
            #     print(f"Error [{src_file}]: {file_hdl_error}")
            print(f"Error [{src_file}]: {file_hdl_error}")
        if w:
            print(f"Warnings [{src_file}]: {w[0].message}")

start_time = time.time()

if args.before and args.after and args.before <= args.after:
	print("Date range is invalid, quitting")
	quit()
else:
    if args.recursive:
        print("scan recursively:")
        try:
            for roots, dirs, files in os.walk(str(args.source_dir), topdown=False):
                for name in files:
                    count += 1
                    handle_file(roots, str(args.target_dir), name)
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("scan the source folder only:")
        try:
            with os.scandir(str(args.source_dir)) as entries:
                for entry in entries:
                    if entry.is_file():
                        count += 1
                        handle_file(str(args.source_dir), str(args.target_dir), entry.name)
        except Exception as e:
            print(f"Error: {e}")
    end_time = time.time()
    print(f"Scanned {count} files, identified {idf_files} and handled {hit_files}")
    print(f"Time elapsed: {end_time - start_time} secs.")