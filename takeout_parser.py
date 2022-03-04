import os
import re
from pathlib import Path
import shutil
from datetime import datetime
import json as jjson
import glob
import subprocess
from subprocess import PIPE, run


# ------------------------------------
# Dictionary that links a media item with a JSON file
takeout_files_dict = {}

# set that contain remaining files. Will be updated after each
takeout_files_json = set()
takeout_files_media_items = set()
takeout_files_other_type = set()
takeout_files_json_lowered = set()

knownExtensionsNew = [".jpg", ".mov", ".jpeg", ".mp4", ".heic", ".png", ".gif", ".bmp", ".avi", ".3gp", ".wmv"]
# ------------------------------------


def organize_google_takout(path):
    global takeout_files_dict
    global takeout_files_media_items
    global takeout_files_json_lowered

    # Validate params
    if not os.path.exists(path):
        raise Exception(path, "Does not exists")

    # ------------------------------------
    # Get all relevant takeout files (Only in Subdir: "Photos from 2019")
    dirs = fast_scandir(path)
    for path in dirs:
        if re.match(r'(Photos from) (\d{4})', Path(path).name):
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                if os.path.splitext(file_path)[1].lower() in knownExtensionsNew:
                    takeout_files_media_items.add(file_path)
                elif os.path.splitext(file_path)[1].lower() == ".json":
                    takeout_files_json.add(file_path)
                    takeout_files_json_lowered.add(file_path.lower())
                else:
                    takeout_files_other_type.add(file_path)

    # ------------------------------------


    # ------------------------------------
    # Match media items with json files
    print_lists()
    match_takeout_guessur()
    match_takeout_guessur_ignore_ext()
    # ------------------------------------

    # ------------------------------------
    # Post checks
    media_items_remove = set()
    for item in takeout_files_media_items:
        # Editet image?
        if "-bearbeitet" in item:
            if item.replace("-bearbeitet", "") in takeout_files_dict:
                json = takeout_files_dict.get(item.replace("-bearbeitet", ""))
                takeout_files_dict[item] = json
                media_items_remove.add(item)
        else:
            for ext in knownExtensionsNew:
                match_name_lower = os.path.splitext(item)[0] + ext
                match_name_upper = os.path.splitext(item)[0] + ext.upper()
                if match_name_lower in takeout_files_dict:
                    json = takeout_files_dict.get(match_name_lower)
                    takeout_files_dict[item] = json
                    media_items_remove.add(item)
                elif match_name_upper in takeout_files_dict:
                    json = takeout_files_dict.get(match_name_upper)
                    takeout_files_dict[item] = json
                    media_items_remove.add(item)

    # 24185
    takeout_files_media_items.difference_update(media_items_remove)
    #for item in takeout_files_media_items:
    #    shutil.copy(item, "\\\\DESKTOP-RUFJNI4\\Users\\Server\\Desktop\\Schnittstelle\\test\\")
    print_lists()
    print(takeout_files_media_items)

    # Write to file system
    with open('C:\\Software\\Python\\pythonProject\\photosApplication\\Image_JSON\\' + datetime.now().strftime('%d_%m_%Y-%H_%M_%S.json'), 'w') as fp:
        jjson.dump(takeout_files_dict, fp)
    # ------------------------------------

def export_takeout():
    # {'modificationTime', 'geoData', 'favorited', 'geoDataExif', 'description', 'photoTakenTime', 'removeResultReason', 'title', 'imageViews', 'googlePhotosOrigin', 'creationTime'}

    #files = glob.glob(os.path.join(os.getcwd(), "Image_JSON", "*.json"))
    #print(files, os.getcwd(), os.path.join(os.getcwd(), "Image_JSON", "*.json"))
    #takeout_files_dict_json = max(files, key=os.path.getctime)
    f = open("C:\\Software\\Python\\pythonProject\\photosApplication\\Image_JSON\\18_01_2021-15_53_08.json")
    takeout_dict = jjson.load(f)
    jsonkeys = set()

    metadata_dict = {}

    i = 0
    for media_pair in takeout_dict.keys():
        file = open(takeout_dict[media_pair])
        json_metadata = jjson.load(file)
        jsonkeys.update(json_metadata.keys())
        #metadata_dict[media_pair]\
        params = {
            "GPSAltitude": json_metadata["geoData"]["altitude"],
            "GPSLatitude": json_metadata["geoData"]["latitude"],
            "GPSLatitudeRef": json_metadata["geoData"]["latitudeSpan"],
            "GPSLongitude": json_metadata["geoData"]["longitude"],
            "GPSLongitudeRef": json_metadata["geoData"]["longitudeSpan"],
            "ImageDescription": json_metadata["description"],
            "Caption-Abstract": json_metadata["description"],
            "DateTimeOriginal": datetime.fromtimestamp(int(json_metadata["photoTakenTime"]["timestamp"])).strftime('%Y:%m:%d %H:%M:%S')
        }
        execute_exiftool(params, media_pair)

        #print(json_metadata)
        #print(json_metadata.keys())
        #print(json_metadata["description"], json_metadata["creationTime"]["formatted"], json_metadata["photoTakenTime"]["formatted"], json_metadata["geoData"])

    print(metadata_dict)
    print(len(takeout_dict))
    print(jsonkeys)


def execute_exiftool(params, filename):

    date_temp = datetime.strptime(params["DateTimeOriginal"], '%Y:%m:%d %H:%M:%S' )
    dirname = "\\\\DESKTOP-RUFJNI4\\Users\\Server\\Desktop\\Schnittstelle\\export\\"+ date_temp.strftime('%Y')+"\\"+ date_temp.strftime('%Y-%m-%d export')+"\\"+os.path.basename(filename)
    #with exiftool.ExifTool() as et:
    #    et.execute(*params2)
    params = '-DateTimeOriginal="%s" ' % params["DateTimeOriginal"] + '-ImageDescription="%s" ' % params["ImageDescription"] +'-Caption-Abstract="%s" ' % params["Caption-Abstract"] + '-GPSAltitude="%s" ' % params["GPSAltitude"] +'-GPSLatitude="%s" ' % params["GPSLatitude"] +'-GPSLatitudeRef="%s" ' % params["GPSLatitudeRef"] +'-GPSLongitude="%s" ' % params["GPSLongitude"] +'-GPSLongitudeRef="%s" ' % params["GPSLongitudeRef"] +'-o "%s" ' % dirname +'"%s"' % filename


    print( "exiftool " + params)
    result = run("exiftool "+ params, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
    print(result.stdout)


def match_takeout_guessur():
    global takeout_files_dict
    global takeout_files_media_items
    global takeout_files_json_lowered

    media_items_remove = set()
    json_remove = set()

    for media_item in takeout_files_media_items:
        # Filnemaes cant be longer than 46 Chars
        media_item_matchname = os.path.join(Path(media_item).parent,
                                            os.path.basename(media_item)[0:46]).lower()

        # 1. Regular match: ./img-123.jpg -> img-123.json.jpg
        if media_item_matchname + ".json" in takeout_files_json_lowered:
            json_match = media_item_matchname + ".json"
            takeout_files_dict[media_item] = json_match
            media_items_remove.add(media_item)
            json_remove.add(json_match)

    takeout_files_media_items.difference_update(media_items_remove)
    takeout_files_json_lowered.difference_update(json_remove)
    print_lists()


    # second stage
    for media_item in takeout_files_media_items:
        # Filnemaes cant be longer than 46 Chars
        media_item_matchname = os.path.join(Path(media_item).parent,
                                            os.path.basename(media_item)[0:46]).lower()
        # Regex match ./img-123(1).jpg -> img-123.jpg(1).json
        media_item_matchname_Obj = re.match(r'(.*)(\(\d\)).(.*)', media_item_matchname)
        if media_item_matchname_Obj and "." + media_item_matchname_Obj.group(3) in knownExtensionsNew:
            json_match = media_item_matchname_Obj.group(1) + "." + media_item_matchname_Obj.group(3) + media_item_matchname_Obj.group(2) + ".json"
            if json_match in takeout_files_json_lowered:
                takeout_files_dict[media_item] = json_match
                media_items_remove.add(media_item)
                json_remove.add(json_match)

    takeout_files_media_items.difference_update(media_items_remove)
    takeout_files_json_lowered.difference_update(json_remove)
    print_lists()


def match_takeout_guessur_ignore_ext():

    global takeout_files_dict
    global takeout_files_media_items
    global takeout_files_json_lowered

    media_items_remove = set()
    json_remove = set()

    for media_item in takeout_files_media_items:
        for ext in knownExtensionsNew:
            # Filnemaes cant be longer than 46 Chars
            media_item_matchname = os.path.join(Path(media_item).parent,
                                                os.path.basename(os.path.splitext(media_item)[0])[0:46]).lower() + ext

            # 1. Regular match: ./img-123.jpg -> img-123.json.jpg
            if media_item_matchname + ".json" in takeout_files_json_lowered:
                json_match = media_item_matchname + ".json"
                takeout_files_dict[media_item] = json_match
                media_items_remove.add(media_item)
                json_remove.add(json_match)

    takeout_files_media_items.difference_update(media_items_remove)
    takeout_files_json_lowered.difference_update(json_remove)
    print_lists()

    # second stage
    for media_item in takeout_files_media_items:
        for ext in knownExtensionsNew:
            # Filnemaes cant be longer than 46 Chars
            media_item_matchname = os.path.join(Path(media_item).parent,
                                                os.path.basename(os.path.splitext(media_item)[0])[0:46]).lower() + ext
            # Regex match ./img-123(1).jpg -> img-123.jpg(1).json
            media_item_matchname_Obj = re.match(r'(.*)(\(\d\)).(.*)', media_item_matchname)
            if media_item_matchname_Obj and "." + media_item_matchname_Obj.group(3) in knownExtensionsNew:
                json_match = media_item_matchname_Obj.group(1) + "." + media_item_matchname_Obj.group(3) + media_item_matchname_Obj.group(2) + ".json"
                if json_match in takeout_files_json_lowered:
                    takeout_files_dict[media_item] = json_match
                    media_items_remove.add(media_item)
                    json_remove.add(json_match)

    takeout_files_media_items.difference_update(media_items_remove)
    takeout_files_json_lowered.difference_update(json_remove)
    print_lists()


def fast_scandir(dirname):
    subfolders= [f.path for f in os.scandir(dirname) if f.is_dir()]
    for dirname in list(subfolders):
        subfolders.extend(fast_scandir(dirname))
    return subfolders


def print_lists():
    global takeout_files_dict
    global takeout_files_media_items
    global takeout_files_json_lowered
    print("Total files:", len(takeout_files_media_items)+len(takeout_files_json_lowered)+len(takeout_files_other_type), "Json Files:", len(takeout_files_json_lowered), "Media Items:",
          len(takeout_files_media_items), "Other types:", len(takeout_files_other_type),
          takeout_files_other_type)


def delete_duplicates():
    exist = 0
    not_exist = 0

    path = "D:\\Bilder Takeout\\Google Fotos"
    dirs = fast_scandir(path)
    for path in dirs:
        if re.match(r'(\d{4}-\d{2}-\d{2}) export', Path(path).name):
            for file in os.listdir(path):
                if os.path.exists(os.path.join(path[:len(path)-7], file)):
                    exist = exist + 1
                    if os.path.isdir(os.path.join("D:\\Bilder Takeout\\export_duplicates", Path(path).parent.name,Path(path).name)) == False:
                        os.makedirs(os.path.join("D:\\Bilder Takeout\\export_duplicates", Path(path).parent.name,Path(path).name));
                    shutil.move(os.path.join(path, Path(file)), os.path.join("D:\\Bilder Takeout\\export_duplicates", Path(path).parent.name,Path(path).name, file));
                else:
                    not_exist = not_exist +1

    print("exist in org:", exist, "not exist in org:", not_exist)


delete_duplicates()
# export_takeout()
#organize_google_takout("\\\\DESKTOP-RUFJNI4\\Users\\Server\\Desktop\\Schnittstelle\\Philipp Takeout\\Takeout")