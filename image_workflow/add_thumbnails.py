from .common import (
    add_thumbnail,
    has_thumbnail,
    iterate_images,
    ALL_SUPPORTED_EXTENSIONS,
)


def add_thumbnails_if_needed(file_path):
    if not has_thumbnail(file_path):
        add_thumbnail(file_path)
    else:
        print(f"Already has thumbnail for {file_path}")


def main():
    extensions = list(ALL_SUPPORTED_EXTENSIONS)
    iterate_images(add_thumbnails_if_needed, extensions)


if __name__ == "__main__":
    main()
