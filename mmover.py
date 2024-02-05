import os, sys, argparse, ffmpeg, mimetypes, warnings, time
from pathlib import Path
from datetime import datetime
from shutil import copyfile, move
from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import Base
from pillow_heif import HeifImagePlugin


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


__version__ = '1.1.0'

parser = argparse.ArgumentParser(description="Filtering and handling media files in specific folder")
parser.add_argument("command", type=str, choices=['copy', 'move'], help="command to execute: \"copy\" or \"move\"")
parser.add_argument("media", type=str, choices=['image', 'video'], help="media type: \"image\" or \"video\"")
parser.add_argument("source_dir", type=Path, help="the path to the source folder which need to be scanned, e.g. \"/Path/to/the/source/folder\"")
parser.add_argument("target_dir", type=Path, help="the path to the target folder which pictures be copied/moved to, e.g. \"/Path/to/the/target/folder\"")
parser.add_argument("-r", "--recursive", action="store_true", help="scan the folders recursively")
parser.add_argument("-d", "--dryrun", action="store_true", help="dry run the command only")
parser.add_argument("-c", "--camera", metavar='MODEL', type=str, help='the model of the camera, e.g."iPhone XS"')
parser.add_argument("-b", "--before", metavar='YYYY-M-D', type=str, help='filter pictures taken before the given date yyyy-m-d 0:00 (excluded the date), e.g. "2000-1-1"')
parser.add_argument("-a", "--after", metavar='YYYY-M-D', type=str, help='filter pictures after the given date yyyy-m-d 0:00 (included the date), e.g."2000-1-1"')
parser.add_argument("--rmcrptpic", action="store_true", help="delete corrupted picture files")
parser.add_argument("-t", "--time", action="store_true", help="show time elapsed")
parser.add_argument("-v", "--version", action="version", version='MediaMover ' + __version__)
args = parser.parse_args()

count = 0
idf_files = 0
hit_files = 0
ffprobe_path = resource_path('ffmpeg/ffprobe')

if args.rmcrptpic and not args.dryrun:
    user_confirm = input("Are you sure you want to delete corrupted files? (y/N)")
    if user_confirm.lower() != 'y':
        sys.exit("Operation aborted.")

if args.before:
    bdate = datetime.strptime(args.before, "%Y-%m-%d")

if args.after:
    adate = datetime.strptime(args.after, "%Y-%m-%d")


def check_type(filepath):
    """
    Check the type of the file based on the file path.

    :param filepath: The path of the file.
    :return: The type of the file (e.g., 'image', 'text', etc.) or None if the type cannot be determined.
    """
    _type, _ = mimetypes.guess_type(filepath)
    if _type:
        return _type.split("/")[0]
    else:
        return None


def deep_get_meta(obj, key):
    """
    Returns the value associated with the given key in a nested dictionary object,
    or None if the key is not found. 

    Args:
        obj: The nested dictionary object to search.
        key: The key to search for within the nested dictionary object.

    Returns:
        The value associated with the given key, or None if the key is not found.
    """
    if key in obj:
        if obj[key]:
            return obj[key]
        else:
            return None
    for k, v in obj.items():
        if isinstance(v, dict):
            item = deep_get_meta(v, key)
            if item is not None:
                return item
    return None


def find_video_date(meta):
    """
    Find the earliest date from the given metadata and return it as a datetime object.
    
    Args:
        meta: A dictionary containing metadata information.

    Returns:
        datetime: The earliest date found in the metadata, or None if no date is found.
    """
    date_mask = "%Y-%m-%dT%H:%M:%S"
    date0 = datetime.strptime(deep_get_meta(meta, 'com.apple.quicktime.creationdate')[:19], date_mask) if deep_get_meta(meta, 'com.apple.quicktime.creationdate') else datetime(9999, 12, 31, 0, 0, 0)
    date1 = datetime.strptime(deep_get_meta(meta, 'creation_time')[:19], date_mask) if deep_get_meta(meta,'creation_time') else datetime(9999, 12, 31, 0, 0, 0)
    date2 = datetime.strptime(deep_get_meta(meta, 'date')[:19], date_mask) if deep_get_meta(meta, 'date') else datetime(9999, 12, 31, 0, 0, 0)
    date = min([date0, date1, date2]) if min([date0, date1, date2]) != datetime(9999, 12, 31, 0, 0, 0) else None
    return date


def handle_file(src_dir, tgt_dir, filename):
    """
    This function handles files from the source directory to the target directory based on certain criteria.
    It takes three parameters: src_dir, tgt_dir, and filename.
    There are no return types specified.
    """
    global idf_files, hit_files, args, adate, bdate, ffprobe_path
    src_file = os.path.join(src_dir, filename)
    tgt_file = os.path.join(tgt_dir, filename)

    with warnings.catch_warnings(record=True) as w:
        try:
            if args.media == 'image' and check_type(src_file) == 'image':
                with Image.open(src_file, 'r') as img:
                    exif = img.getexif()
                    if exif:
                        model = exif.get(272)
                        date = datetime.strptime(exif.get(306)[:19], "%Y:%m:%d %H:%M:%S") if exif.get(306) else None
                    else:
                        return
            elif args.media == 'video' and check_type(src_file) == 'video':
                metadata = ffmpeg.probe(src_file, cmd=ffprobe_path)
                if metadata:
                    model = deep_get_meta(metadata, 'com.apple.quicktime.model')
                    date = find_video_date(metadata)
                else:
                    return
            else:
                return
            if not args.camera or (model and model == args.camera):
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
        except Exception as file_hdl_error:
            if args.rmcrptpic and (isinstance(file_hdl_error, UnidentifiedImageError) or (isinstance(file_hdl_error, OSError) and file_hdl_error.args[0] == "Truncated File Read")):
                if args.dryrun:
                    print(f"[Dry run]Would delete from source directory: {filename}")
                else:
                    os.remove(src_file)
                    print(f"Deleted [{filename}] from source directory: {file_hdl_error}")
            else:
                print(f"Error [{src_file}]: {file_hdl_error}")
            return
        if w:
            print(f"Warnings [{src_file}]: {w[0].message}")

if args.time:
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
    print(f"Scanned {count} files, identified {idf_files} and handled {hit_files}")
    if args.time:
        end_time = time.time()
        print(f"Time elapsed: {end_time - start_time} secs.")
