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
    # TODO: find a way to not do it manually
    pass


def _remove_dsstore(dir):
    for root, dirs, files in os.walk(dir):
        for name in files:
            if name == ".DS_Store":
                print(os.path.join(root, name))
                os.remove(os.path.join(root, name))


def verify_archives(total):
    for i in range(1, total + 1):
        archive = f"takeout-20201108T103354Z-{i:03d}.zip"
        command = f"unzip -qt {archive}"
        print(archive, os.path.getsize(archive))
        subprocess.check_call(command.split())


def extract_archives():
    for i, archive in enumerate(sorted(glob.glob('takeout*.zip'))):
        targetdir = os.path.splitext(archive)[0]
        if not os.path.exists(targetdir):
            # command = f"unzip -q -d {targetdir} {archive}"
            # print(command)
            # subprocess.check_call(command.split())
            # https://github.com/adamhathcock/sharpcompress/issues/315#issuecomment-409894957
            # https://github.com/CocoaPods/CocoaPods/issues/7711#issuecomment-386942543
            command = f"ditto -V -x -k --sequesterRsrc --rsrc {archive} {targetdir}"
            print(command)
            subprocess.check_call(command.split())  # , stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def print_merge_commands():
    targetfolder = "/Volumes/Photos/Google Photos/"
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


def move_edited_to_original():
    for root, dirs, files in os.walk("."):
        for name in files:
            if "-edited." in name:
                edited = os.path.join(root, name)
                original = edited.replace("-edited", "")
                print(f"{edited} --> {os.path.basename(original)}")
                shutil.move(edited, original)


def move_parenthesis_json():
    pattern = r'(.*)\.(\w+)(\(\d\))\.json'
    for root, dirs, files in os.walk("."):
        for name in files:
            m = re.match(pattern, name)
            if m:
                newname = f"{m[1]}{m[3]}.{m[2]}.json"
                print(f"{os.path.join(root, name)} -> {newname}")
                # shutil.move(os.path.join(root, name), os.path.join(root, newname))


def print_exiftool_command():
    archive_dirs = ['Google Photos']
    for archive in archive_dirs:
        _remove_dsstore(archive)
    image_extensions = " ".join([f"-ext {format}" for format in image_formats])
    video_extensions = " ".join([f"-ext {format}" for format in video_formats])
    for ext in [image_extensions, video_extensions]:
        for archive in archive_dirs:
            print(f"exiftool -m -@ {exif_config} {ext} '{archive}' 2>errors_videos.log")


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
