from library_organizer import read_google_photos, read_manifest, retrieve_metadata, check_manifest_result,\
    update_google_photos_images


def perform_sync():
    tcur = datetime.now()

    manifest = read_manifest()

    check_manifest_result(manifest)

    update_google_photos_images(manifest)

    # update_google_photos_images()
    print(f"Total time passed {(datetime.now() - tcur).total_seconds()} s")



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--sync', help='Sync local Picasa files to Google Photos', action="store_true")
    args = parser.parse_args()

    if args.sync:
        perform_sync