import tifffile
import json
import os
from pathlib import Path
from .common import iterate_images, get_sha1, get_existing_metadata


def compress_tiff(file_path):
    file_path = Path(file_path)
    output_file = file_path.with_name(f"{file_path.stem}-compressed.tiff")

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

    try:
        with tifffile.TiffFile(file_path) as tif:
            arr = tif.asarray()
            page = tif.pages[0]
            photometric = getattr(page, "photometric", 2)

            # Preserve resolution if available
            resolution = None
            if "XResolution" in page.tags and "YResolution" in page.tags:
                xres = page.tags["XResolution"].value
                yres = page.tags["YResolution"].value
                # resolution unit?
                unit = (
                    page.tags["ResolutionUnit"].value
                    if "ResolutionUnit" in page.tags
                    else 2
                )
                resolution = (xres, yres, unit)

            # Check for thumbnail
            thumb_arr = None
            thumb_photometric = None

            if page.subifds:
                thumb_offsets = set(page.subifds)
                for series in tif.series:
                    if series.pages and series.pages[0].offset in thumb_offsets:
                        thumb_arr = series.asarray()
                        thumb_photometric = series.pages[0].photometric
                        break

        # Write new file
        with tifffile.TiffWriter(output_file) as writer:
            has_thumb = thumb_arr is not None

            writer.write(
                arr,
                photometric=photometric,
                compression="LZW",
                subifds=1 if has_thumb else 0,
                resolution=resolution,
                description=json_str,
            )

            if has_thumb:
                writer.write(
                    thumb_arr,
                    photometric=thumb_photometric,
                    subfiletype=1,
                    compression="LZW",
                )

        # Preserve timestamps
        os.utime(output_file, (stat.st_atime, stat.st_mtime))

        output_file.replace(file_path)
        print(f"Compressed {file_path}")
    except Exception as e:
        print(f"Failed to compress {file_path}: {e}")
        if output_file.exists():
            output_file.unlink()


def main():
    extensions = [".tif", ".tiff"]
    iterate_images(compress_tiff, extensions)


if __name__ == "__main__":
    main()
