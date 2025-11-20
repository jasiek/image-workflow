import argparse
import subprocess
import json
import os
from pathlib import Path
from .common import iterate_images, get_sha1, get_existing_metadata


def convert_to_format(file_path, target_format):
    file_path = Path(file_path)
    if "converted" in file_path.parts:
        return

    # Gather metadata
    stat = file_path.stat()

    existing_meta = get_existing_metadata(file_path)
    if existing_meta:
        json_str = json.dumps(existing_meta)
    else:
        created_at = getattr(stat, "st_birthtime", stat.st_mtime)
        sha1 = get_sha1(file_path)
        source_file = str(file_path.resolve())

        metadata = {"created_at": created_at, "sha1": sha1, "source_file": source_file}
        json_str = json.dumps(metadata)

    base = file_path.stem
    dir_path = file_path.parent
    converted_dir = Path("converted") / dir_path
    converted_dir.mkdir(parents=True, exist_ok=True)
    new_file = converted_dir / f"{base}.{target_format}"

    try:
        # Add comment with JSON metadata
        subprocess.run(
            ["gm", "convert", str(file_path), "-comment", json_str, str(new_file)],
            check=True,
        )

        # Preserve timestamps (atime, mtime)
        os.utime(new_file, (stat.st_atime, stat.st_mtime))

        print(f"Converted {file_path} to {new_file}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to convert {file_path}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Convert images to target format")
    parser.add_argument("target_format", help="Target format (e.g., png)")
    args = parser.parse_args()

    extensions = [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"]

    def func(file_path):
        convert_to_format(file_path, args.target_format)

    iterate_images(func, extensions)


if __name__ == "__main__":
    main()
