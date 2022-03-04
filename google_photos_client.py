import os
from Modules.Google import Create_Service
import pandas as pd# pip install pandas
import requests # pip install requests
import pickle
import pprint
from datetime import datetime
import json
import datetime     # for general datetime object handling
import rfc3339      # for date object -> date string
import iso8601      # for date string -> date object

from numpy.linalg import lstsq

CLIENT_SECRET_FILE = "client_secret.json"
API_NAME = 'photoslibrary'
API_VERSION = 'v1'
SCOPES = ['https://www.googleapis.com/auth/photoslibrary', 'https://www.googleapis.com/auth/photoslibrary.sharing', 'https://www.googleapis.com/auth/photoslibrary.edit.appcreateddata']
upload_url = 'https://photoslibrary.googleapis.com/v1/uploads'

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)



def upload_image(image_path, token):
    """
    Upload bytes of a single image

    :param image_path: filesystem path of image
    :param token: API auth token
    :return: API response
    """
    headers = {
        'Authorization': 'Bearer ' + token.token,
        'Content-type': 'application/octet-stream',
        'X-Goog-Upload-Protocol': 'raw'
    }

    img = open(image_path, 'rb').read()
    response = requests.post(upload_url, data=img, headers=headers)
    return response


def upload_images_final(images):
    """
    Method for bulk uploading images to GPhotos.
    If the image has tags (EXIF Subjects) they will be written into the decription

    :param images: list() of images -> image_name = {
    :return:
    """
    # step 1: Upload byte data to Google Server
    token = pickle.load(open('token_photoslibrary_v1.pickle', 'rb'))
    upload_list = []

    counter = 0
    for key, value in images.items():
        target_path = value["target"]
        response = upload_image(target_path, token)
        counter += 1
        print(f"uploaded: {counter}, remaining: {len(images)}")

        if value["tags"] != "":
            # tags -> description field
            upload_list.append({'description': value["tags"],
                                'simpleMediaItem': {'uploadToken': response.content.decode('utf-8'),
                                                 'fileName': value["name"]}})
        else:
            upload_list.append({'simpleMediaItem': {'uploadToken': response.content.decode('utf-8'),
                                                 'fileName': value["name"]}})

    # Build request body
    request_body = {
        'newMediaItems': upload_list
    }
    upload_response = service.mediaItems().batchCreate(body=request_body).execute()



def get_all_images_new():
    """
    Due to a bug in the GPhotos implementation the "list" function does not work
    instead the "search" function is used
    :return: all media items from library including GPhotos Id & Timestamp
    """

    media_item_list = []
    media_item_dict = {}

    nextpagetoken = 'Dummy'
    while nextpagetoken != '':
        nextpagetoken = '' if nextpagetoken == 'Dummy' else nextpagetoken
        results = service.mediaItems().search(
                body = {
                    "filters": {
                        "dateFilter":{
                            "ranges": [
                                {
                                    "startDate": {
                                        "day": 1,
                                        "month": 1,
                                        "year": 1000
                                    },
                                    "endDate": {
                                        "day": 1,
                                        "month": 1,
                                        "year": 3000
                                    }
                                }
                            ]
                        }
                    },
                    "pageSize": 100, # The maximum pageSize is 100.
                    "pageToken": nextpagetoken
                }).execute()

        if results.get('mediaItems', []):
            items = results.get('mediaItems', [])
            item_infos = dict()
            for item in items:
                item_infos['date'] = iso8601.parse_date(item['mediaMetadata']['creationTime'])
                item_infos['id'] = item['id']
                media_item_dict[item['filename']] = item_infos
        nextpagetoken = results.get('nextPageToken', '')

    return media_item_dict



def update_image():
    id = "AC90cofK_UvQ91PQ3uViPpvRYo6vpv8X2476H5m7CnERdbqiOiitaF5vwBJP0G1WqonY8V6QizXq6k2DUzsZlzbIHESplrj4ow"
    response = service.mediaItems().get(mediaItemId=id).execute()
    img_instance = response
    pprint.pprint(img_instance)
    img_instance["description"] = "test 2"
    img_instance["filename"] = "test1234.jpg"
    #img_instance["mediaMetadata"]['creationTime'] = '2021-05-21T10:10:01Z'

    response = service.mediaItems().patch(id=id, updateMask="filename", body=img_instance).execute()

    print(response)


if __name__ == '__main__':

    get_all_images()

    lstAlbums = []
    nextPageToken = 'Dummy'
    while nextPageToken != '':
        nextPageToken = '' if nextPageToken == 'Dummy' else nextPageToken

        response = service.albums().list(
            pageSize=50,
            excludeNonAppCreatedData=False,
            pageToken=nextPageToken
        ).execute()

        if response.get('albums'):
            for element in response.get('albums'):
                lstAlbums.append(element["title"])
        nextPageToken = response.get('nextPageToken', '')

    with open('album_list.txt', 'w', encoding="UTF-8") as f:
        for item in lstAlbums:
            f.write("%s\n" % item)
    #for element in lstAlbums:
    #    print(element["title"])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--readPicasaManifest', help='Read the picasa export Manifest', action="store_true")
    parser.add_argument('-e', '--exportLibrary', help='Export folders listed in Picasa Manifest ', action="store_true")
    args = parser.parse_args()

    if args.readPicasaManifest:
        picasa_manifest_dir


    if args.exportLibrary:
        print("Export Library")
        populate_picasa_manifest()
        print(picasa_manifest)
    #print(args.excelFilePath)
    #if args.excelFilePath is None or not os.path.isfile(args.excelFilePath):