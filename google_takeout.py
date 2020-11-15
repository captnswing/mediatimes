import os
import glob
import shutil
import subprocess

video_formats = ['.3gp', '.avi', '.mov', '.mp4', '.mpg']
image_formats = ['.gif', '.heic', '.jpeg', '.jpg', '.png']


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


def verify_archives():
    for i in range(1, 149):
        archive = f"takeout-20201108T103354Z-{i:03d}.zip"
        command = f"unzip -qt {archive}"
        print(archive, os.path.getsize(archive))
        subprocess.check_call(command.split())


def find_extensions():
    extensions = set()
    for root, dirs, files in os.walk("."):
        for name in files:
            extension = os.path.splitext(name)[1]
            if extension == ".zip" or extension == "":
                continue
            extensions.add(extension.lower())
    print(sorted(extensions))


def merge_edited():
    for root, dirs, files in os.walk("."):
        for name in files:
            if "-edited." in name:
                edited = os.path.join(root, name)
                original = edited.replace("-edited", "")
                print(f"{edited} --> {os.path.basename(original)}")
                shutil.move(edited, original)


def remove_dsstore(dir):
    for root, dirs, files in os.walk(dir):
        for name in files:
            if name == ".DS_Store":
                print(os.path.join(root, name))
                os.remove(os.path.join(root, name))


def exif_fix_archive_images():
    archive_dirs = sorted([d for d in os.listdir(".") if os.path.isdir(d) and d.startswith("takeout-")])
    # archive_dirs = sorted([d for d in os.listdir(".") if os.path.isdir(d) and d.startswith("19")])
    a = archive_dirs[0]
    remove_dsstore(a)
    command = f"exiftool -@ /Users/frahof/Development/private/iphoto-google/exif_args_images.cfg {a}"
    print(command)
    try:
        stderr_output = subprocess.check_call(command.split())#, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        print("Status : FAIL", exc.returncode, exc.output)
    else:
        print(stderr_output)


def exif_fix_archive_videos():
    archive_dirs = sorted([d for d in os.listdir(".") if os.path.isdir(d) and d.startswith("takeout-")])
    # archive_dirs = sorted([d for d in os.listdir(".") if os.path.isdir(d) and d.startswith("19")])
    a = archive_dirs[0]
    remove_dsstore(a)
    command = f"exiftool -@ /Users/frahof/Development/private/iphoto-google/exif_args_videos.cfg {a}"
    print(command)
    try:
        stderr_output = subprocess.check_call(command.split())#, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        print("Status : FAIL", exc.returncode, exc.output)
    else:
        print(stderr_output)


if __name__ == "__main__":
    DATA_DIR = "/Volumes/Photos"
    # DATA_DIR = "/Users/frahof/Development/private/iphoto-google/"
    os.chdir(DATA_DIR)
    # verify_archives
    # extract_archives()
    # find_extensions()
    # merge_edited()
    exif_fix_archive_videos()
