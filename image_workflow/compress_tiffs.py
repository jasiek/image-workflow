import tifffile
from pathlib import Path
from .common import iterate_images


def compress_tiff(file_path):
    file_path = Path(file_path)
    output_file = file_path.with_name(f"{file_path.stem}-compressed.tiff")
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
            )

            if has_thumb:
                writer.write(
                    thumb_arr,
                    photometric=thumb_photometric,
                    subfiletype=1,
                    compression="LZW",
                )

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
