from .common import (
    has_thumbnail,
    iterate_images,
    remove_thumbnail,
    ALL_SUPPORTED_EXTENSIONS,
)


def remove_thumbnails_if_needed(file_path):
    if has_thumbnail(file_path):
        remove_thumbnail(file_path)
    else:
        print(f"No thumbnail to remove for {file_path}")


def main():
    extensions = list(ALL_SUPPORTED_EXTENSIONS)
    iterate_images(remove_thumbnails_if_needed, extensions)


if __name__ == "__main__":
    main()
