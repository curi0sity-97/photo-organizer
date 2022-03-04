import datetime
import os
import subprocess
from subprocess import PIPE, run
import shutil
import exif
import exiftool
import csv
import sys
import re

class ExiftoolAdaptor:

    def __init__(self, source_dir, dest_dir):
        self.source_dir = source_dir
        self.dest_dir = dest_dir

    def change_exif_data(self, images):

        # Check if file already exists in upload folder
        for image_path, data in images.items():

            target_path = image_path.replace(self.source_dir, self.dest_dir)
            images[image_path]["target"] = target_path

            # If file does not exist, create dir and copy2 image
            if not os.path.isfile(target_path):
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(image_path, target_path)

            # Change dates
            try:
                with open(target_path, 'rb') as test:
                    my_image = exif.Image(test)
            except Exception:
                raise Exception(f"problem with opening {target_path}")

            # Remove these tags as Google Photos cannot interpret them
            remove_list = ["subsec_time", "subsec_time_digitized", "subsec_time_original"]
            for element in remove_list:
                try:
                    my_image.delete(element)
                except AttributeError:
                    pass

            date_formatted = data["date"].strftime("%Y:%m:%d %H:%M:%S")
            my_image.datetime = date_formatted
            my_image.datetime_digitized = date_formatted
            my_image.datetime_original = date_formatted

            with open(target_path, 'wb') as updated_image:
                updated_image.write(my_image.get_file())

        return images


    def get_tags(self, images):
        with exiftool.ExifTool() as et:
            metadata = et.get_tags_batch(["Subject"], images.keys())

        for tag in metadata:
            tags = ""
            if 'XMP:Subject' in tag:
                print(tag['XMP:Subject'], type(tag['XMP:Subject']))
                if isinstance(tag['XMP:Subject'], list):
                    tags = set(tag['XMP:Subject'])
                    tags.discard("NOLOC")
                    tags.discard("NOTAG")
                    tags.discard("NOTAG*NOLOC")
                    tags = "; ".join(list(tags))
                elif isinstance(tag['XMP:Subject'], str):
                    if tag['XMP:Subject'] not in ("NOLOC", "NOTAG", "NOTAG*NOLOC"):
                        tags = tag['XMP:Subject']
            images[tag["SourceFile"].replace("/", "\\")]["tags"] = tags

        return images


    def exif_change_batch(self, images):

        tag_dict = {
            ".jpg": ["DateTimeOriginal", "CreateDate", "FileCreateDate"],
            ".jpeg": ["DateTimeOriginal", "CreateDate", "FileCreateDate"],
            ".mp4": ["TrackCreateDate", "MediaCreateDate", "FileCreateDate"],
            ".mov": ["TrackCreateDate", "MediaCreateDate", "FileCreateDate"],
            ".avi": ["MetadataDate", "CreateDate", "DateCreated", "FileCreateDate", # .avi adobe movie tags
                     "CreationDate", "MediaCreateDate", "TrackCreateDate"], # .avi iphone export tags

            ".jpg_remove": ["SubSecCreateDate", "SubSecDateTimeOriginal", "SubSecModifyDate"],
            ".jpeg_remove": ["SubSecCreateDate", "SubSecDateTimeOriginal", "SubSecModifyDate"]
        }

        output = "SourceFile,Keywords\n"

        for key, value in images.items():

            # Set target path for image
            target_path = key.replace(self.source_dir, self.dest_dir)
            images[key]["target"] = target_path

            # If file does not exist, create dir and copy2 image
            if not os.path.isfile(target_path):
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(image_path, target_path)

            params = ""
            date = value["date"].strftime('%Y:%m:%d %H:%M:%S')
            ext = os.path.splitext(key)[1].lower()

            if ext in tag_dict:
                for tag in tag_dict[ext]:
                    params += f'-{tag}="{date}", '
            else:
                raise Exception(f"Unknow file type: {os.path.splitext(key)[1].lower()}")
            if ext + "_remove" in tag_dict:
                for tag in tag_dict[ext + "_remove"]:
                    params += f'-{tag}= , '

            output += f'{target_path},"{params[:-2]}"\n'

        path = ""
        with open('output_batch.csv', 'w', encoding='UTF8', newline='') as f:
            path = os.path.relpath(f.name)
            f.write(output)

        result = run(f'exiftool -csv="{path}" -sep=", " -r -overwrite_original "{self.dest_dir}"', stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
        updated = re.search(r'(\d+) (image files updated)', result.stderr)

        if not updated:
            raise Exception(result.stderr)

        if updated.group(1) != str(len(images)):
            raise Exception(f" Error, {updated.group(1)} updated, but {len(images)} in list")

        os.remove('output_batch.csv')


    def exiftoolChangeDate(self, image_path, date_new ): #image, dateStr, day

        target_path = image_path.replace(self.source_dir, self.dest_dir)

        date = datetime.strptime(date_new, '%Y-%m-%d %H:%M:%S')

        extensionDict = {
            ".jpg": '-SubSecCreateDate= ' +
                    '-SubSecDateTimeOriginal= ' +
                    '-SubSecModifyDate= ' +
                    '-DateTimeOriginal="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-CreateDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-ModifyDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-FileCreateDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S')+
                    '-FileModifyDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S')+
                    '-SubSecCreateDate= '+
                    '-SubSecDateTimeOriginal= '+
                    '-SubSecModifyDate= '+
                    '-o "%s" ' % target_path +
                    '"%s"' % image_path,

            ".jpeg":'-SubSecCreateDate= ' +
                    '-SubSecDateTimeOriginal= ' +
                    '-SubSecModifyDate= ' +
                    '-DateTimeOriginal="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-CreateDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-ModifyDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-FileCreateDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S')+
                    '-FileModifyDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S')+
                    '-o "%s" ' % target_path +
                    '"%s"' % image_path,

            ".mov": '-DateTimeOriginal="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-ModifyDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-CreateDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-FileCreateDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S')+
                    '-FileModifyDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S')+
                    '-TrackCreateDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-TrackModifyDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-MediaCreateDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-MediaModifyDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-o "%s" ' % target_path +
                    '"%s"' % image_path,
            ".mp4": '-DateTimeOriginal="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-ModifyDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-CreateDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-FileCreateDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S')+
                    '-FileModifyDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S')+
                    '-TrackCreateDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-TrackModifyDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-MediaCreateDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-MediaModifyDate="%s" ' % date.strftime('%Y:%m:%d %H:%M:%S') +
                    '-o "%s" ' % target_path +
                    '"%s"' % image_path
        }

        if not os.path.splitext(image_path)[1].lower() in extensionDict.keys():
            raise Exception(os.path.splitext(image_path)[1].lower(), "Has not been added yet")

        params = extensionDict.get(os.path.splitext(image_path)[1].lower())


        result = run("exiftool "+ params, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)

        if result.stderr == '':
            print("no error")
        elif "JPEG EOI marker not found" in result.stderr:
                raise Exception("Error while converting:", resultNew.stderr)

        elif "Warning: [minor] Entries in IFD0 were out of sequence. Fixed." in result.stderr:
            print("Warning: [minor] Entries in IFD0 were out of sequence")

        else:
            raise Exception("Other error:", result.stderr)

        return target_path
