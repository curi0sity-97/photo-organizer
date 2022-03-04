# Photo Organizer
![tagging](logo.png)

Since Google Deprecated the Picasa API in 2019 synchronizing changes from
a local filesystem photolibrary to the Google Photos application is no more possible.

## Features:
- Retrieving information from the Picasa desktop application (through PicasaManifest.xml)
- Retrieving image metadata using EXIFtool (tags and GPS location)

## Instructions:
1. Enable Google Photos API and export client secret file (see more at
   [Google Photos API](https://developers.google.com/photos/library/guides/get-started) documentation) <br>
   save the secret file in the application folder as client_secret.json
   
2. Create a Backup in Picasa of the complete library (save to local filesystem)<br>
Set Path to PicassaManifest.xml file in


## Sync to Gphotos
### Enable custom Image order
![tagging](https://cdn.icon-icons.com/icons2/936/PNG/72/sort-reverse-alphabetical-order_icon-icons.com_73401.png)

This functions objective is to recreate the custom image order that is archived by arranging
images inside folders in the Picasa application.
Google Photos  orders images by date and only allows a custom order inside albums (new to old).
To bypass this issue the Timestamps of the media items must be changed arccordingly. 

### Making tagging available in Google Photos
![tagging](https://cdn.icon-icons.com/icons2/936/PNG/72/tags_icon-icons.com_73382.png)

Unfortunatley Google Photos does not provide tagging functionionality on it's own.
In this application tags (<i>XMP:Subject</i>) from the local images are written into 
the Google Photos description field and therefore become available in the search function.

### Preserve Geo Location
![tagging](https://cdn.icon-icons.com/icons2/653/PNG/72/locate_gps_navigation_pin_point_location_icon-icons.com_59906.png)

Picasa provides easy functionality for edditing the location of single or multiple photos.
This application ensures that those changes will be applied during the upload to Google Photos.