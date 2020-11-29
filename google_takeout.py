import os
import glob
import shutil
import subprocess
import re

ROOTDIR = os.path.abspath(os.path.dirname(__file__))

video_formats = ['.3gp', '.mov', '.mp4', '.mpg', '.m4v', 'wmv']  # '.m2ts', '.avi' cannot be written by exiftool yet
image_formats = ['.gif', '.heic', '.jpeg', '.jpg', '.png', '.tiff', 'tif']
exif_config = os.path.join(ROOTDIR, "exif_args.cfg")


def download_archives():
    # TODO: find a way to do it automatically ¯\_(ツ)_/¯
    pass


def _remove_dsstore(dir):
    for root, dirs, files in os.walk(dir):
        for name in files:
            if name == ".DS_Store":
                print(os.path.join(root, name))
                os.remove(os.path.join(root, name))


def _remove_directories_with_only_one_json_file(dir):
    print("""find . -type d -exec bash -c "echo -ne '{} '; ls '{}' | wc -l" \; | awk '$NF==1' >r""")
    print("cat r | awk '{print $1}' | xargs rm -rf {};")


def _find_and_remove_corrup_heic(dir):
    for root, dirs, files in os.walk(dir):
        for name in files:
            if not name.lower().endswith(".heic"):
                continue
            command = f"identify '{os.path.join(root, name)}' >/dev/null 2>&1"
            rc = subprocess.call(command, shell=True)
            if rc:
                print(f"'{os.path.join(root, name)}'")


def verify_archives(tag, total, compression):
    for i in range(1, total + 1):
        archive = f"takeout-{tag}-{i:03d}.{compression}"
        if compression == "zip":
            command = f"unzip -qt {archive}"
        elif compression == "tgz":
            command = f"tar tfz {archive}"
        print(archive, os.path.getsize(archive))
        subprocess.check_call(command.split())


def extract_archives(compression):
    for i, archive in enumerate(sorted(glob.glob(f"takeout*.{compression}"))):
        targetdir = os.path.splitext(archive)[0]
        if not os.path.exists(targetdir):
            if compression == "zip":
                # command = f"unzip -q -d {targetdir} {archive}"
                # print(command)
                # subprocess.check_call(command.split())
                # https://github.com/adamhathcock/sharpcompress/issues/315#issuecomment-409894957
                # https://github.com/CocoaPods/CocoaPods/issues/7711#issuecomment-386942543
                command = f"ditto -V -x -k --sequesterRsrc --rsrc {archive} {targetdir}"
            elif compression == "tgz":
                dir = archive.rstrip('.tgz')
                os.mkdir(f"{dir}")
                command = f"tar xfz {archive} -C {dir}"
            print(command)
            subprocess.check_call(command.split())  # , stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def print_merge_commands():
    targetfolder = os.path.abspath(os.path.join(os.path.curdir, "Google Photos/"))
    archive_dirs = sorted([d for d in os.listdir(".") if os.path.isdir(d) and d.startswith("takeout-")])
    for archive in archive_dirs:
        merge_command = f"ditto '{archive}/Takeout/Google Photos' '{targetfolder}'"
        print(f"echo '{archive}'")
        print(merge_command)


def find_extensions():
    extensions = set()
    for root, dirs, files in os.walk("."):
        for name in files:
            extension = os.path.splitext(name)[1]
            if extension == ".zip" or extension == "":
                continue
            extensions.add(extension.lower())
    print(sorted(extensions))


def _find_original_file(edited_file):
    # './Google Photos/2015-04-22-23/IMG_2079-edited.jpg' --> './Google Photos/2015-04-22-23/IMG_2079.JPG'
    original_base = edited_file.replace("-edited", "").replace("-redigerad", "")
    candidates = glob.glob(f"{os.path.splitext(original_base)[0]}*")
    original = [c for c in candidates if not (c.endswith(".json") or "-redigerad" in c or "-edited" in c)]
    return original


def move_edited_to_original():
    for root, dirs, files in os.walk("."):
        for name in files:
            if name.endswith(".json"):
                continue
            elif "-edited" in name or "-redigerad" in name:
                edited = os.path.join(root, name)
                original = _find_original_file(edited)
                try:
                    print(f"{edited} --> {os.path.basename(original[0])}")
                    shutil.move(edited, original[0])
                except IndexError:
                    print("-" * 50)
                    print(f"skipping {edited}")
                    print("-" * 50)
            elif "(1)." in name:
                edited = os.path.join(root, name)
                base, ext = os.path.splitext(edited)
                if not ext in image_formats:
                    continue
                print(_find_original_file(edited))


def move_parenthesis_json():
    pattern = r'(.*)\.(\w+)(\(\d\))\.json'
    for root, dirs, files in os.walk("."):
        for name in files:
            m = re.match(pattern, name)
            if m:
                newname = f"{m[1]}{m[3]}.{m[2]}.json"
                print(f"{os.path.join(root, name)} -> {newname}")
                shutil.move(os.path.join(root, name), os.path.join(root, newname))


def print_exiftool_command(archive):
    exif_types = {
        "images": " ".join([f"-ext {format}" for format in image_formats]),
        "videos": " ".join([f"-ext {format}" for format in video_formats])
    }
    for type, extensions in exif_types.items():
        print(f"exiftool -m -@ {exif_config} {extensions} '{archive}' 2>errors_{type}.log")


def find_duplicates():
    pass


def correct_image_errors():
    for line in open("errors_images.log"):
        fn, ext = os.path.splitext(line.split(" - ")[1].strip())
        filename = os.path.join(os.path.abspath("."), fn)
        extension = ".jpg"
        if "Not a valid HEIC (looks more like a JPEG)" in line:
            if os.path.exists(f"{filename + ext}"):
                shutil.move(f"{filename + ext}", f"{filename}{extension}")
            if os.path.exists(filename + ext + ".json"):
                shutil.move(f"{filename + ext}.json", f"{filename}{extension}.json")
        elif "Not a valid PNG (looks more like a JPEG)" in line:
            if os.path.exists(f"{filename + ext}"):
                shutil.move(f"{filename + ext}", f"{filename}{extension}")
            if os.path.exists(filename + ext + ".json"):
                shutil.move(f"{filename + ext}.json", f"{filename}{extension}.json")
        else:
            continue
        subprocess.call([
            "exiftool",
            "-@",
            "/Users/frahof/Development/private/iphoto-google/exif_args.cfg",
            f"{filename}{extension}"
        ])


def correct_video_errors():
    for line in open("errors_videos.log"):
        fn, ext = os.path.splitext(line.split(" - ")[1].strip())
        filename = os.path.join(os.path.abspath("."), fn)
        if "Warning: Error opening file" in line and ext == ".json":
            # e2165bff3800a379c3ffcfe489af3ab6.MOV
            # e2165bff3800a379c3ffcfe489af3ab6.json
            base, ext = os.path.splitext(filename)
            if ext == ".MOV":
                shutil.move(f"{base}.json", f"{fn}.json")
                subprocess.call([
                    "exiftool",
                    "-@",
                    "/Users/frahof/Development/private/iphoto-google/exif_args.cfg",
                    f"{fn}"
                ])

        else:
            continue


if __name__ == "__main__":
    DATA_DIR = "/Volumes/Photos"
    # DATA_DIR = "/Users/frahof/Development/private/iphoto-google/"
    os.chdir(DATA_DIR)
    # download_archives()
    # verify_archives(148)
    # extract_archives()
    # print_merge_commands()
    # find_extensions()
    # move_edited_to_original()
    # move_parenthesis_json()
    # correct_image_errors()
    # correct_video_errors()
    # print_exiftool_command()
    # find_duplicates()
