import os

from .common import iterate_images, extract_thumbnail, ALL_SUPPORTED_EXTENSIONS


def extract_thumbnail_to_dir(file_path):
    thumb_dir = "thumbnails"
    if not os.path.exists(thumb_dir):
        os.makedirs(thumb_dir)
    return extract_thumbnail(file_path, thumb_dir)


def main():
    extensions = list(ALL_SUPPORTED_EXTENSIONS)
    iterate_images(extract_thumbnail_to_dir, extensions)


if __name__ == "__main__":
    main()
