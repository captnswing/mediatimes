import glob
import json
import os
import shutil
import subprocess

import arrow

ROOTDIR = os.path.abspath(os.path.dirname(__file__))

video_formats = [
    ".3gp",
    ".avi",
    ".m2ts",
    ".m4v",
    ".mov",
    ".mp4",
    ".mpg",
    ".wmv",
]  # '.m2ts', '.avi' cannot be written by exiftool yet
image_formats = [".gif", ".heic", ".jpeg", ".jpg", ".png", ".tiff", ".tif"]


# ['.3gp', '.avi', '.gif', '.heic', '.html', '.jpeg', '.jpg', '.json', '.m2ts', '.m4v', '.mov', '.mp4', '.mpg', '.png', '.tiff']


def download_archives():
    # TODO: find a way to do it automatically ¯\_(ツ)_/¯
    pass


def verify_archives(tag, total, compression):
    for i in range(1, total + 1):
        archive = f"takeout-{tag}-{i:03d}.{compression}"
        if compression == "zip":
            command = f"unzip -qt {archive}"
        elif compression == "tgz":
            command = f"tar tfz {archive}"
        else:
            return
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
            else:
                return
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


def move_subfolders_into_batches(dir):
    os.chdir(dir)
    dircontents = os.listdir(".")
    dircontents = [d for d in dircontents if not d.startswith("batch_")]
    batchnumber = 10
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
    # download_archives()
    # verify_archives("20201123T165802Z", 32, "tgz")
    # extract_archives("zip")
    find_extensions()
    # move_subfolders_into_batches('Google Photos')
