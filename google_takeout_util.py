import glob
import json
import os
import re
import shutil
import subprocess
from itertools import groupby

import arrow

ROOTDIR = os.path.abspath(os.path.dirname(__file__))

video_formats = [
    ".3gp",
    ".mov",
    ".mp4",
    ".mpg",
    ".m4v",
    "wmv",
    ".m2ts",
    ".avi",
]  # '.m2ts', '.avi' cannot be written by exiftool yet
image_formats = [".gif", ".heic", ".jpeg", ".jpg", ".png", ".tiff", "tif"]
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
    print(
        """find . -type d -exec bash -c "echo -ne '{} '; ls '{}' | wc -l" \; | awk '$NF==1' >r"""
    )
    print("cat r | awk '{print $1}' | xargs rm -rf {};")


def _find_and_remove_corrupt_heic(dir):
    for root, dirs, files in os.walk(dir):
        for name in files:
            if not name.lower().endswith(".heic"):
                continue
            command = f"identify '{os.path.join(root, name)}' >/dev/null 2>&1"
            rc = subprocess.call(command, shell=True)
            if rc:
                print(f"'{os.path.join(root, name)}'")
                os.remove(os.path.join(root, name))


def _find_original_file(edited_file):
    # './Google Photos/2015-04-22-23/IMG_2079-edited.jpg' --> './Google Photos/2015-04-22-23/IMG_2079.JPG'
    original_base = edited_file.replace("-edited", "").replace("-redigerad", "")
    candidates = glob.glob(f"{os.path.splitext(original_base)[0]}*")
    original = [
        c
        for c in candidates
        if not (c.endswith(".json") or "-redigerad" in c or "-edited" in c)
    ]
    return original


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
                os.mkdir(f"{targetdir}")
                command = f"tar xfz {archive} -C {targetdir}"
            print(command)
            subprocess.check_call(
                command.split()
            )  # , stdout=subprocess.PIPE, stderr=subprocess.PIPE)


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


def move_parenthesis_json():
    pattern = r"(.*)\.(\w+)(\(\d\))\.json"
    for root, dirs, files in os.walk("."):
        for name in files:
            m = re.match(pattern, name)
            if m:
                newname = f"{m[1]}{m[3]}.{m[2]}.json"
                print(f"{os.path.join(root, name)} -> {newname}")
                shutil.move(os.path.join(root, name), os.path.join(root, newname))


def cleanup():
    _remove_dsstore(".")
    _remove_directories_with_only_one_json_file(".")
    _find_and_remove_corrupt_heic(".")
    # find . -type f | egrep '\.\.json'


def _run_exiftool_videos(fn, d=None):
    if not d:
        data = json.loads(open(f"{fn}.json").read())
        d = arrow.get(data["photoTakenTime"]["timestamp"], "X")
    s = subprocess.check_output(
        [
            "exiftool",
            "-m",
            "-tagsFromFile",
            "%d/%f.%e.json",
            "-overwrite_original",
            "-progress",
            "-GPSAltitude<GeoDataAltitude",
            "-GPSLatitude<GeoDataLatitude",
            "-GPSLatitudeRef<GeoDataLatitude",
            "-GPSLongitude<GeoDataLongitude",
            "-GPSLongitudeRef<GeoDataLongitude",
            "-Keywords<Tags",
            "-Subject<Tags",
            "-Caption-Abstract<Description",
            "-ImageDescription<Description",
            f"-CreateDate<{d}",
            fn,
        ]
    )
    print(s)


def _run_exiftool_images(fn):
    command = [
        "exiftool",
        "-d",
        "%s",
        "-tagsFromFile",
        "%d/%f.%e.json",
        "-overwrite_original",
        "-progress",
        "-GPSAltitude<GeoDataAltitude",
        "-GPSLatitude<GeoDataLatitude",
        "-GPSLatitudeRef<GeoDataLatitude",
        "-GPSLongitude<GeoDataLongitude",
        "-GPSLongitudeRef<GeoDataLongitude",
        "-Keywords<Tags",
        "-Subject<Tags",
        "-Caption-Abstract<Description",
        "-ImageDescription<Description",
        "-DateTimeOriginal<PhotoTakenTimeTimestamp",
        fn,
    ]
    # print(" ".join(command))
    try:
        s = subprocess.check_output(command, encoding="utf-8")
    except subprocess.CalledProcessError:
        pass
    print(s)


def print_dates(g):
    for fn in g:
        if os.path.splitext(fn)[1] == ".json":
            continue
        exif_data = subprocess.check_output(
            ["/usr/local/bin/exiftool", "-alldates", "-j", fn]
        )
        exif_data = json.loads(exif_data)[0]
        try:
            print(f"{fn:150} {exif_data['DateTimeOriginal']}")
        except:
            print(f"{fn:150} {exif_data['CreateDate']}")


def move_subfolders_into_batches(dir):
    os.chdir(dir)
    dircontents = os.listdir(".")
    dircontents = [d for d in dircontents if not d.startswith("batch_")]
    batchnumber = 30
    batchsize = int(len(dircontents) / batchnumber) + 1
    for i in range(batchnumber):
        batchdir = f"batch_{i + 1:03d}"
        s = slice(i * batchsize, (i + 1) * batchsize - 1)
        print(batchdir, s)
        if not os.path.exists(batchdir):
            os.mkdir(batchdir)
        for item in dircontents[s]:
            shutil.move(item, batchdir)
        print("-" * 50)


if __name__ == "__main__":
    DATA_DIR = "/Volumes/Photos/frank/"
    os.chdir(DATA_DIR)
    download_archives()
    # verify_archives("20201123T165802Z", 32, "tgz")
    # extract_archives("zip")
    find_extensions()
    # cleanup()
    # move_edited_to_original()
    # move_parenthesis_json()
    # move_subfolders_into_batches('Google Photos')
