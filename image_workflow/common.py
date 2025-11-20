import os
import shutil
from io import BytesIO
from pathlib import Path

import piexif
import tifffile
from PIL import Image

# Processor classes for different image formats


class ExifImageProcessor:
    @staticmethod
    def has_thumbnail(file_path):
        try:
            exif = piexif.load(str(file_path))
            return exif["thumbnail"] is not None
        except:
            return False

    @staticmethod
    def add_thumbnail(file_path):
        file_str = str(file_path)
        if not os.path.isfile(file_path):
            return False
        with Image.open(file_str) as img:
            thumb = img.resize((256, 256))
            buffer = BytesIO()
            thumb.save(buffer, "JPEG")
            thumb_bytes = buffer.getvalue()

        try:
            exif_dict = piexif.load(file_str)
        except:
            # Create new EXIF with thumbnail
            exif_dict = {"thumbnail": thumb_bytes}
            print(f"Added thumbnail to {file_path}: created new EXIF segment")
        exif_dict["thumbnail"] = thumb_bytes
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, file_str)
        print(f"Added thumbnail to {file_path}")
        return True

    @staticmethod
    def extract_thumbnail(file_path, thumb_dir):
        file_str = str(file_path)
        try:
            exif = piexif.load(file_str)
            if exif["thumbnail"] is not None:
                thumb_path = os.path.join(
                    thumb_dir, f"{os.path.basename(file_str)}.jpg"
                )
                with open(thumb_path, "wb") as f:
                    f.write(exif["thumbnail"])
                print(f"Extracted thumbnail for {file_path}")
                return True
            else:
                print(f"No thumbnail found in {file_path}")
                return False
        except Exception as e:
            print(f"Failed to extract thumbnail for {file_path}: {e}")
            return False

    @staticmethod
    def remove_thumbnail(file_path):
        file_str = str(file_path)
        try:
            exif_dict = piexif.load(file_str)
            if exif_dict["thumbnail"] is not None:
                exif_dict["thumbnail"] = None
                exif_bytes = piexif.dump(exif_dict)
                piexif.insert(exif_bytes, file_str)
                print(f"Removed thumbnail from {file_path}")
                return True
            else:
                print(f"No thumbnail to remove in {file_path}")
                return False
        except Exception as e:
            print(f"Failed to remove thumbnail from {file_path}: {e}")
            return False


class PngImageProcessor:
    @staticmethod
    def has_thumbnail(file_path):
        sidecar = str(file_path) + ".thumb.jpg"
        return os.path.isfile(sidecar)

    @staticmethod
    def add_thumbnail(file_path):
        file_str = str(file_path)
        if not os.path.isfile(file_path):
            return False
        if PngImageProcessor.has_thumbnail(file_path):
            return False
        with Image.open(file_str) as img:
            thumb = img.resize((256, 256))
            buffer = BytesIO()
            thumb.save(buffer, "JPEG")
            thumb_bytes = buffer.getvalue()

        sidecar = file_str + ".thumb.jpg"
        with open(sidecar, "wb") as f:
            f.write(thumb_bytes)
        print(f"Added thumbnail to {file_path}")
        return True

    @staticmethod
    def extract_thumbnail(file_path, thumb_dir):
        file_str = str(file_path)
        sidecar = file_str + ".thumb.jpg"
        if not os.path.isfile(sidecar):
            print(f"No thumbnail found in {file_path}")
            return False
        thumb_path = os.path.join(thumb_dir, f"{os.path.basename(file_str)}.jpg")
        shutil.copy2(sidecar, thumb_path)
        print(f"Extracted thumbnail for {file_path}")
        return True

    @staticmethod
    def remove_thumbnail(file_path):
        file_str = str(file_path)
        sidecar = file_str + ".thumb.jpg"
        if not os.path.isfile(sidecar):
            print(f"No thumbnail to remove in {file_path}")
            return False
        os.remove(sidecar)
        print(f"Removed thumbnail from {file_path}")
        return True


class TiffImageProcessor:
    @staticmethod
    def has_thumbnail(file_path):
        try:
            with tifffile.TiffFile(file_path) as tif:
                # Check for SubIFD thumbnail (correct method)
                if tif.pages[0].subifds:
                    return True
                # Fallback: check for multi-page (legacy method compatibility)
                # only if second page is a thumbnail (e.g. reduced resolution)
                # For now, we'll strictly check for the SubIFD structure as the "correct" way
                # but since we are fixing it, we might want to be able to detect the old ones too?
                # Let's stick to the new standard to avoid false positives with actual multipage TIFFs.
                return False
        except:
            return False

    @staticmethod
    def add_thumbnail(file_path):
        file_str = str(file_path)
        if not os.path.isfile(file_path):
            return False
        if TiffImageProcessor.has_thumbnail(file_path):
            return False

        # Generate thumbnail
        with Image.open(file_str) as img:
            thumb = img.resize((256, 256))
            # We need the array for tifffile, so we can just get it from PIL
            thumb_arr = np.array(thumb) if "np" in globals() else None
            # If numpy is not imported globally, we can still rely on PIL -> BytesIO -> tifffile to get array
            # or just use numpy if available. common.py doesn't import numpy.
            # Let's use the existing approach to get the array safely without adding numpy dependency if possible,
            # but tifffile uses numpy arrays so numpy is definitely available implicitly or explicitly.
            # Tifffile returns numpy arrays.

            buffer = BytesIO()
            thumb.save(buffer, "TIFF")
            thumb_bytes = buffer.getvalue()

        # Read original
        with tifffile.TiffFile(file_path) as tif:
            arr = tif.asarray()
            page0 = tif.pages[0]
            photometric = getattr(page0, "photometric", 2)  # RGB
            compression = getattr(page0, "compression", 1)  # uncompressed
            # Preserve other critical tags if needed, but for now these are the basics used before

        tmp_path = file_str + ".tmp"
        try:
            # Write original with SubIFD pointing to thumbnail
            with tifffile.TiffWriter(tmp_path) as writer:
                # subifds=1 means we promise 1 subifd for this page
                writer.write(
                    arr, photometric=photometric, compression=compression, subifds=1
                )

                # Load thumb as array
                with BytesIO(thumb_bytes) as bio:
                    thumbs = tifffile.TiffFile(bio)
                    thumb_arr = thumbs.asarray()
                    thumb_photometric = thumbs.pages[0].photometric or 2

                # Write the thumbnail as the SubIFD
                # subfiletype=1 indicates it is a reduced-resolution version (thumbnail)
                writer.write(thumb_arr, photometric=thumb_photometric, subfiletype=1)

            os.replace(tmp_path, file_str)
            print(f"Added thumbnail to {file_path}")
            return True
        except Exception as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            print(f"Failed to add thumbnail to {file_path}: {e}")
            return False

    @staticmethod
    def extract_thumbnail(file_path, thumb_dir):
        file_str = str(file_path)
        try:
            with tifffile.TiffFile(file_path) as tif:
                # Check SubIFDs of first page
                page = tif.pages[0]
                if not page.subifds:
                    print(f"No thumbnail found in {file_path}")
                    return False

                # Find the series matching the subifd offset
                thumb_offsets = set(page.subifds)
                thumb_series = None

                # Look through series to find the one that matches the subifd offset
                for series in tif.series:
                    if series.pages:
                        if series.pages[0].offset in thumb_offsets:
                            thumb_series = series
                            break

                if thumb_series is None:
                    print(f"Could not locate thumbnail series in {file_path}")
                    return False

                thumb_data = thumb_series.asarray()

                thumb_path = os.path.join(
                    thumb_dir, f"{os.path.basename(file_str)}.jpg"
                )
                thumb_img = Image.fromarray(thumb_data)
                thumb_img.save(thumb_path, "JPEG")
                print(f"Extracted thumbnail for {file_path}")
                return True
        except Exception as e:
            print(f"Failed to extract thumbnail for {file_path}: {e}")
            return False

    @staticmethod
    def remove_thumbnail(file_path):
        file_str = str(file_path)
        # We don't check has_thumbnail here strictly to allow cleaning up potentially malformed ones
        # providing we can read the main image.

        try:
            with tifffile.TiffFile(file_path) as tif:
                if not tif.pages[0].subifds:
                    print(f"No thumbnail to remove in {file_path}")
                    return False

                arr = tif.pages[0].asarray()
                photometric = getattr(tif.pages[0], "photometric", 2)
                compression = getattr(tif.pages[0], "compression", 1)

            tmp_path = file_str + ".tmp"
            # Write back only standard image, no subifds
            tifffile.imwrite(
                tmp_path, arr, photometric=photometric, compression=compression
            )
            os.replace(tmp_path, file_str)
            print(f"Removed thumbnail from {file_path}")
            return True
        except Exception as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            print(f"Failed to remove thumbnail from {file_path}: {e}")
            return False


PROCESSORS = {
    ".jpg": ExifImageProcessor,
    ".jpeg": ExifImageProcessor,
    ".tif": TiffImageProcessor,
    ".tiff": TiffImageProcessor,
    ".png": PngImageProcessor,
}


EXIF_SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".tif", ".tiff")
ALL_SUPPORTED_EXTENSIONS = EXIF_SUPPORTED_EXTENSIONS + (".png",)


def has_thumbnail(file_path):
    """Check if image has embedded thumbnail or sidecar."""
    ext = Path(file_path).suffix.lower()
    processor = PROCESSORS.get(ext)
    if not processor:
        return False
    return processor.has_thumbnail(file_path)


def add_thumbnail(file_path):
    """Add a thumbnail to an image (embedded or sidecar)."""
    ext = Path(file_path).suffix.lower()
    processor = PROCESSORS.get(ext)
    if not processor:
        raise ValueError(f"Unsupported image format for thumbnail operations: {ext}")
    return processor.add_thumbnail(file_path)


def extract_thumbnail(file_path, thumb_dir):
    """Extract thumbnail to thumb_dir (from embedded or sidecar)."""
    ext = Path(file_path).suffix.lower()
    processor = PROCESSORS.get(ext)
    if not processor:
        raise ValueError(f"Unsupported image format for thumbnail operations: {ext}")
    return processor.extract_thumbnail(file_path, thumb_dir)


def remove_thumbnail(file_path):
    """Remove embedded thumbnail or sidecar."""
    ext = Path(file_path).suffix.lower()
    processor = PROCESSORS.get(ext)
    if not processor:
        raise ValueError(f"Unsupported image format for thumbnail operations: {ext}")
    return processor.remove_thumbnail(file_path)


def iterate_images(func, extensions):
    """Iterate over image files in subdirectories and apply func sequentially."""
    files = []
    for ext in extensions:
        files.extend(Path(".").rglob(f"*{ext}"))

    for file in files:
        func(file)
