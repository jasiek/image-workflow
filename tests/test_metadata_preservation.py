import os
import shutil
import tempfile
import json
import subprocess
import hashlib
import pytest
import tifffile
from pathlib import Path
from image_workflow.convert_format import convert_to_format
from image_workflow.compress_tiffs import compress_tiff


def test_convert_format_metadata():
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            os.chdir(tmpdir)

            # Setup source
            SRC = Path("test.jpg")
            # Create dummy image
            subprocess.run(
                ["gm", "convert", "-size", "100x100", "xc:white", str(SRC)], check=True
            )

            # Set mtime
            mtime = 1600000000.0
            os.utime(SRC, (mtime, mtime))

            # Convert
            convert_to_format(SRC, "png")

            DST = Path("converted") / "test.png"
            assert DST.exists()

            # Check mtime
            dst_stat = DST.stat()
            assert (
                abs(dst_stat.st_mtime - mtime) < 1.0
            ), f"mtime mismatch: {dst_stat.st_mtime} vs {mtime}"

            # Check Description/Comment
            # Read using gm identify usually shows it as Comment
            res = subprocess.run(
                ["gm", "identify", "-verbose", str(DST)],
                capture_output=True,
                text=True,
                check=True,
            )

            assert "created_at" in res.stdout
            assert "sha1" in res.stdout
            assert str(SRC.resolve()) in res.stdout  # source_file

        finally:
            os.chdir(original_cwd)


def test_compress_tiff_metadata():
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            os.chdir(tmpdir)

            SRC = Path("test.tif")
            # Create dummy tiff
            data = b"testdata" * 100  # small data
            # Use tifffile to write initial tiff
            # (Assuming create a valid tiff image)
            import numpy as np

            arr = np.zeros((10, 10, 3), dtype=np.uint8)
            tifffile.imwrite(SRC, arr, photometric="rgb")

            # Set mtime
            mtime = 1650000000.0
            os.utime(SRC, (mtime, mtime))

            # SHA1 of original
            sha1 = hashlib.sha1()
            with open(SRC, "rb") as f:
                sha1.update(f.read())
            orig_sha1 = sha1.hexdigest()

            # Compress
            compress_tiff(SRC)

            # Check mtime
            # In-place replacement
            dst_stat = SRC.stat()
            assert (
                abs(dst_stat.st_mtime - mtime) < 1.0
            ), "mtime not preserved after compression"

            # Check Description tag
            with tifffile.TiffFile(SRC) as tif:
                page = tif.pages[0]
                desc = page.description
                assert desc is not None

                # Parse JSON
                meta = json.loads(desc)
                assert meta["sha1"] == orig_sha1
                assert meta["source_file"] == str(SRC.resolve())
                # creation time check might vary by ms, but should match original's stat

        finally:
            os.chdir(original_cwd)


def test_metadata_chain_of_custody():
    """
    Verify that metadata referring to the original file is preserved across multiple transformations.
    """
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            os.chdir(tmpdir)
            from image_workflow.common import add_thumbnail, get_existing_metadata

            # 1. Create Original Source (A)
            SRC_A = Path("original.jpg")
            subprocess.run(
                ["gm", "convert", "-size", "100x100", "xc:red", str(SRC_A)], check=True
            )

            mtime_a = 1500000000.0
            os.utime(SRC_A, (mtime_a, mtime_a))

            # Calc SHA1 of A
            sha1_a = hashlib.sha1()
            with open(SRC_A, "rb") as f:
                sha1_a.update(f.read())
            orig_sha1_a = sha1_a.hexdigest()

            # 2. Convert A -> B (PNG)
            # This creates converted/original.png
            convert_to_format(SRC_A, "png")
            SRC_B = Path("converted/original.png")
            assert SRC_B.exists()

            # Verify B has metadata of A
            meta_b = get_existing_metadata(SRC_B)

            # Debugging if None
            if meta_b is None:
                res_c = subprocess.run(
                    ["gm", "identify", "-format", "%c", str(SRC_B)],
                    capture_output=True,
                    text=True,
                )
                print(f"\nDEBUG gm %c output: {repr(res_c.stdout)}")

                res = subprocess.run(
                    ["gm", "identify", "-verbose", str(SRC_B)],
                    capture_output=True,
                    text=True,
                )
                print("\nDEBUG gm identify output:\n", res.stdout)

            assert meta_b is not None
            assert meta_b["sha1"] == orig_sha1_a
            assert meta_b["source_file"] == str(SRC_A.resolve())

            # 3. Transform B (Add Thumbnail)
            add_thumbnail(SRC_B)

            # Verify B still points to A
            meta_b_new = get_existing_metadata(SRC_B)
            assert meta_b_new is not None
            assert (
                meta_b_new["sha1"] == orig_sha1_a
            ), "Metadata should refer to original A, not B's previous state"
            assert meta_b_new["source_file"] == str(SRC_A.resolve())

            # 4. Compress B (if it was TIFF)
            # Let's do A -> TIFF -> Compress
            convert_to_format(SRC_A, "tif")
            SRC_TIF = Path("converted/original.tif")

            # Verify TIF has metadata of A
            with tifffile.TiffFile(SRC_TIF) as tif:
                desc = tif.pages[0].description
                meta_c = json.loads(desc)
                assert meta_c["sha1"] == orig_sha1_a

            # Compress TIF
            compress_tiff(SRC_TIF)

            # Verify Compressed TIF still points to A
            with tifffile.TiffFile(SRC_TIF) as tif:
                desc = tif.pages[0].description
                meta_d = json.loads(desc)
                assert (
                    meta_d["sha1"] == orig_sha1_a
                ), "Compressed TIFF should preserve original metadata"

        finally:
            os.chdir(original_cwd)


def test_add_thumbnail_preserves_metadata():
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            os.chdir(tmpdir)
            from image_workflow.common import add_thumbnail, has_thumbnail

            # --- Test TIFF ---
            SRC_TIFF = Path("test_add.tif")
            import numpy as np

            arr = np.zeros((10, 10, 3), dtype=np.uint8)
            tifffile.imwrite(SRC_TIFF, arr, photometric="rgb")

            mtime_tiff = 1680000000.0
            os.utime(SRC_TIFF, (mtime_tiff, mtime_tiff))

            # Get original SHA1 to verify
            sha1_h = hashlib.sha1()
            with open(SRC_TIFF, "rb") as f:
                sha1_h.update(f.read())
            sha1_tiff = sha1_h.hexdigest()

            add_thumbnail(SRC_TIFF)

            # Check mtime preservation
            stat_tiff = SRC_TIFF.stat()
            assert (
                abs(stat_tiff.st_mtime - mtime_tiff) < 1.0
            ), "TIFF mtime not preserved after add_thumbnail"

            # Check description
            with tifffile.TiffFile(SRC_TIFF) as tif:
                desc = tif.pages[0].description
                assert desc is not None
                meta = json.loads(desc)
                assert meta["sha1"] == sha1_tiff
                assert meta["source_file"] == str(SRC_TIFF.resolve())

            # --- Test JPG (Exif) ---
            SRC_JPG = Path("test_add.jpg")
            subprocess.run(
                ["gm", "convert", "-size", "100x100", "xc:white", str(SRC_JPG)],
                check=True,
            )

            mtime_jpg = 1690000000.0
            os.utime(SRC_JPG, (mtime_jpg, mtime_jpg))

            # Get original SHA1
            sha1_h = hashlib.sha1()
            with open(SRC_JPG, "rb") as f:
                sha1_h.update(f.read())
            sha1_jpg = sha1_h.hexdigest()

            add_thumbnail(SRC_JPG)

            # Check mtime preservation
            stat_jpg = SRC_JPG.stat()
            assert (
                abs(stat_jpg.st_mtime - mtime_jpg) < 1.0
            ), "JPG mtime not preserved after add_thumbnail"

            # Check Description using gm identify or piexif
            # gm identify -verbose shows "Image Description" or similar
            # or "Profile-exif: ... unknown structure" depending on gm version
            # Easier to use piexif to read back manually or use gm if consistent

            # Let's try piexif reading since that's what wrote it
            import piexif

            exif = piexif.load(str(SRC_JPG))
            # Tag 270 is ImageDescription
            desc_bytes = exif["0th"].get(piexif.ImageIFD.ImageDescription)
            assert desc_bytes is not None
            desc_str = desc_bytes.decode("utf-8")
            meta_jpg = json.loads(desc_str)
            assert meta_jpg["sha1"] == sha1_jpg

        finally:
            os.chdir(original_cwd)
