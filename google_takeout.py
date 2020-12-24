import json
import os
import glob
import shutil
import subprocess
import re
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


def print_merge_commands():
    targetfolder = os.path.abspath(os.path.join(os.path.curdir, "Google Photos/"))
    archive_dirs = sorted(
        [d for d in os.listdir(".") if os.path.isdir(d) and d.startswith("takeout-")]
    )
    for archive in archive_dirs:
        merge_command = f"ditto '{archive}/Takeout/Google Photos' '{targetfolder}'"
        print(f"echo '{archive}'")
        print(merge_command)


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


def correct_image_errors():
    for line in open("errors_images.log"):
        fn, ext = os.path.splitext(line.split(" - ")[1].strip())
        filename = os.path.join(os.path.abspath("."), fn)
        extension = ".jpg"
        if (
            "Not a valid HEIC (looks more like a JPEG)" in line
            or "Not a valid PNG (looks more like a JPEG)" in line
        ):
            if os.path.exists(f"{filename + ext}"):
                shutil.move(f"{filename + ext}", f"{filename}{extension}")
            if os.path.exists(filename + ext + ".json"):
                shutil.move(f"{filename + ext}.json", f"{filename}{extension}.json")
        else:
            continue
        _run_exiftool_images(f"{filename}{extension}")


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
                _run_exiftool_videos(fn)
        else:
            continue


def walk_videos(dir):
    os.chdir(dir)
    now = arrow.get(2020, 11, 11, 11, 11, 11)
    for root, dirs, files in os.walk("."):
        for name in files:
            fn = os.path.join(root, name)
            extension = os.path.splitext(name)[1]
            if not extension.lower() in video_formats:
                continue
            s = subprocess.check_output(
                [
                    "exiftool",
                    "-m",
                    # unsure if this is right: CreateDate?
                    # "-CreateDate",
                    "-DateTimeOriginal",
                    f"{fn}",
                ],
                encoding="utf-8",
            )
            date_exiftool = s.split(" : ")[-1].strip()
            print(date_exiftool)
            try:
                date_exiftool = arrow.get(date_exiftool, "YYYY:MM:DD HH:mm:ss")
            except (arrow.parser.ParserMatchError, ValueError):
                print(fn, date_exiftool)
                date_exiftool = now
            if os.path.exists(f"{fn}.json"):
                data = json.loads(open(f"{fn}.json").read())
                date_googlejson = arrow.get(data["photoTakenTime"]["timestamp"], "X")
            else:
                # json doesn't exist
                # remove media file?
                date_googlejson = now
            diff = (date_exiftool - date_googlejson).days
            if diff >= 1:
                print(
                    f"{fn:70s} {date_exiftool.datetime:%Y-%m-%d %H:%M}\t\t{date_googlejson.datetime:%Y-%m-%d %H:%M}\t\t{diff}"
                )
                try:
                    _run_exiftool_videos(fn, date_googlejson)
                except:
                    continue


def walk_images(dir):
    os.chdir(dir)
    now = arrow.get(2020, 11, 11, 11, 11, 11)
    for root, dirs, files in os.walk("."):
        for name in files:
            fn = os.path.join(root, name)
            extension = os.path.splitext(name)[1]
            if not extension.lower() in image_formats:
                continue
            s = subprocess.check_output(
                ["exiftool", "-m", "-DateTimeOriginal", f"{fn}"], encoding="utf-8"
            )
            date_exiftool = s.split(" : ")[-1].strip()
            try:
                date_exiftool = arrow.get(date_exiftool, "YYYY:MM:DD HH:mm:ss")
            except (arrow.parser.ParserMatchError, ValueError):
                print(fn, date_exiftool)
                date_exiftool = now
            if os.path.exists(f"{fn}.json"):
                data = json.loads(open(f"{fn}.json").read())
                date_googlejson = arrow.get(data["photoTakenTime"]["timestamp"], "X")
            else:
                # json doesn't exist
                # remove media file?
                date_googlejson = now
            diff = (date_exiftool - date_googlejson).days
            if diff >= 1:
                print(
                    f"{fn:110s} {date_exiftool.datetime:%Y-%m-%d %H:%M}\t\t{date_googlejson.datetime:%Y-%m-%d %H:%M}\t\t{diff}"
                )
                try:
                    _run_exiftool_images(fn)
                except:
                    continue


def remove_duplicates():
    print(f"fdupes -rdN 'Google Photos' >dupes")
    # https://stackoverflow.com/a/49567096
    with open("dupes") as f:
        group = []
        for line in f:
            if line.strip():
                group.append(line.strip())
            else:
                print_dates(group)
                print("-" * 50)
                group = []
        if group:
            print_dates(group)
            print("-" * 50)
    # original = lines[0::2]
    # copy = lines[1::2]
    # print(len(original), len(copy))


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
    # DATA_DIR = "/Users/frahof/Development/private/iphoto-google/"
    os.chdir(DATA_DIR)
    # download_archives()
    # verify_archives("20201123T165802Z", 32, "tgz")
    extract_archives("zip")
    # find_extensions()
    #
    # print_merge_commands()
    # cleanup()
    # move_edited_to_original()
    # move_parenthesis_json()
    #
    # walk_images('Google Photos')
    # correct_image_errors()
    #
    # walk_videos('Google Photos')
    # correct_video_errors()
    #
    # remove_duplicates()
    # move_subfolders_into_batches('Google Photos')
