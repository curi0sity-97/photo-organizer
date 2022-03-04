import os
from xml.dom import minidom
import re
from datetime import datetime, timedelta
import json
import pathlib
import ntpath
import pprint
import exiftool
from exif import Image
import ast
import shutil
import collections
from database_handler import photos_db
from exiftool_adaptor import ExiftoolAdaptor
from itertools import islice
from google_photos_client import upload_images_final, get_all_images_new
import send2trash
from collections import OrderedDict


# list of media file extensions recognized by picasa
known_extensions = [".jpg", ".mov", ".jpeg", ".mp4", ".png", ".gif", ".bmp", ".avi", "3gp", ".wmv"]

picasa_manifest_dir = r"C:\Users\Public\Documents\Picasa\PicasaManifest.xml"
picasa_library_dir = r"D:\Bilder Takeout\Google Fotos"
upload_dir = r"D:\Bilder Takeout\Upload To Google Photos"


def read_google_photos():
    """

    :return:
    """
    # get dicts
    google_photos_dict = get_all_images_new()
    picasa_dict = read_manifest()

    return  google_photos_dict, picasa_dict


def read_manifest():
    """

    :return: manifest_dict: name -> filepath
                            folder -> image folder (corresponds to album)
                            index -> position in folder (corresponds to album position)
                            date -> picasa date
    """
    manifest_dict = OrderedDict()

    if not os.path.isfile(picasa_manifest_dir):
        raise Exception("No picasa Manifest found at:", picasa_manifest_dir)

    fileList = minidom.parse(picasa_manifest_dir).getElementsByTagName('file')

    date_dict = dict()
    counter = 0
    for file in fileList:
        path = pathlib.Path(file.getElementsByTagName("path")[0].firstChild.data.replace("\[","").replace("]", ":"))
        date_match = re.match("(\d{4}-\d{2}-\d{2})", path.parent.name)

        if path.suffix.lower() in known_extensions and date_match:
            name = ntpath.basename(path)
            date = datetime.strptime(date_match.group(0), '%Y-%m-%d').date()
            if date in date_dict.keys():
                date_dict[date] = date_dict[date]+1
            else:
                date_dict[date] = 1
            counter += 1

            # retrieve following information
            manifest_dict[os.path.normpath(path)] = {
                "name": name,
                "folder": date,
                "index": date_dict[date],
                "date":  datetime(date.year, date.month, date.day, hour=12) + timedelta(minutes=date_dict[date])
            }

    return manifest_dict


def retrieve_metadata(manifest):
    """
    Retrieves Tags and GPS information

    :param manifest:
    :return:
    """
    with exiftool.ExifTool() as et:
        metadata = et.get_metadata_batch(files)

    for record in metadata:
        dict = json.dumps(record)
        name = ntpath.basename(record["SourceFile"])
        if "XMP:Subject" in record:
            manifest[name]["tags"] = record["XMP:Subject"]
        if "EXIF:GPSLongitude" in record:
            manifest[name]["gps_longitude"] = record["EXIF:GPSLongitude"]
        if "EXIF:GPSLatitude" in record:
            manifest[name]["gps_latitude"] = record["EXIF:GPSLatitude"]

    return manifest


def update_google_photos_images(manifest):
    """
    This meth

    :param manifest:
    :return:
    """
    # Exiftool copy & update
    exiftool_adaptor = ExiftoolAdaptor(r"D:\Bilder Takeout\Google Fotos", "D:\gphotos upload test")

    # Uses Exif tool to change Dates of images, copies them to target if neccessary
    manifest = exiftool_adaptor.exif_change_batch(manifest)

    # Retrieves tags for images
    manifest = exiftool_adaptor.get_tags(manifest)

    # upload the Image
    upload_images_final(manifest)

    # Delete temp copied image
    send2trash.send2trash(target_path)


def check_manifest_result(manifest):
    """
    This method ensures that there is no missmatch between local media lib and PicasaManifest file
    :param manifest:
    :return:
    """
    check_dict = OrderedDict()
    for dirpath, dirs, files in os.walk(picasa_library_dir):
        relpath = os.path.relpath(dirpath, picasa_library_dir)
        if re.match(r"\d{4}(.*)", relpath) and " export" not in relpath and ".picasaoriginals" not in relpath:
            files_amount = 0
            file_ext_unknown = set()
            files = set(files)
            files_final = set()
            files.discard(".picasa.ini")
            for file in files:
                if os.path.splitext(file)[1].lower() in known_extensions:
                    files_amount += 1
                    files_final.add(file)
                else:
                    file_ext_unknown.add(os.path.splitext(file)[1].lower())


            if files_amount > 0:
                content = {
                    "files_amount": files_amount,
                    "file_ext_unknown": file_ext_unknown,
                    "files": files_final

                }
                check_dict[relpath] = content

    manifest_dict = OrderedDict()
    temp_files = set()


    for key, value in manifest.items():
        folder = value["folder"].strftime('%Y-%m-%d')
        if folder not in manifest_dict:
            manifest_dict[folder] = set()
            manifest_dict[folder].add(key)
        else:
            manifest_dict[folder].add(key)

    not_included = []
    ok = []
    size_missmatch = []
    for key, value in check_dict.items():
        basename = os.path.basename(key)
        if basename in manifest_dict:
            if value["files_amount"] == len(manifest_dict[basename]):
                ok.append(f'OK: {key}, {value["files_amount"]} Manifest: {len(manifest_dict[basename])}')
            else:
                size_missmatch.append(f'SIZE MISSMATCH: {key}, {value["files_amount"]} Manifest: {len(manifest_dict[basename])}'
                      f' {value["files"].difference(manifest_dict[basename])}'
                      f'\nfilesys: {value["files"]}, mainifest: {manifest_dict[basename]}')
        else:
            not_included.append(f'NOT INCLUDED: {key} not in manifest')

    for element in ok:
        print(element)

    for element in size_missmatch:
        print(element)

    for element in not_included:
        print(element)

    if size_missmatch or not_included:
        raise Exception("Error in Picasa Manifest")
















