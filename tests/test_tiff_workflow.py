import os
import pytest
import shutil
import tempfile
import tifffile
from image_workflow.common import (
    TiffImageProcessor,
    add_thumbnail,
    has_thumbnail,
    extract_thumbnail,
    remove_thumbnail,
)
from image_workflow.compress_tiffs import compress_tiff

TEST_IMAGE_DIR = "test_images"
CLEAN_TIFF = os.path.join(TEST_IMAGE_DIR, "clean_sample.tif")


def test_tiff_thumbnail_lifecycle():
    """
    Verify TiffImageProcessor correctly handles the lifecycle of a thumbnail:
    add -> check -> extract -> remove.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Prepare test file
        test_tif = os.path.join(tmpdir, "test.tif")
        shutil.copy2(CLEAN_TIFF, test_tif)

        # 1. Initial state
        assert not has_thumbnail(test_tif), "Clean sample should not have thumbnail"

        # 2. Add thumbnail
        assert add_thumbnail(test_tif) is True, "add_thumbnail failed"
        assert (
            has_thumbnail(test_tif) is True
        ), "has_thumbnail should be True after adding"

        # Verify structure explicitly (SubIFD check)
        with tifffile.TiffFile(test_tif) as tif:
            # Expecting page 0 to have subifds
            assert tif.pages[0].subifds, "Page 0 should have subifds"

        # 3. Extract thumbnail
        thumb_out_dir = os.path.join(tmpdir, "thumbs")
        os.makedirs(thumb_out_dir)
        assert (
            extract_thumbnail(test_tif, thumb_out_dir) is True
        ), "extract_thumbnail failed"

        extracted_thumb_path = os.path.join(thumb_out_dir, "test.tif.jpg")
        assert os.path.exists(extracted_thumb_path), "Extracted thumbnail file missing"
        assert (
            os.path.getsize(extracted_thumb_path) > 0
        ), "Extracted thumbnail file is empty"

        # 4. Remove thumbnail
        assert remove_thumbnail(test_tif) is True, "remove_thumbnail failed"
        assert not has_thumbnail(
            test_tif
        ), "has_thumbnail should be False after removal"

        # Verify structure explicitly
        with tifffile.TiffFile(test_tif) as tif:
            assert not tif.pages[
                0
            ].subifds, "Page 0 should not have subifds after removal"


def test_tiff_compression_preservation():
    """
    Verify that compressing a TIFF with `compress_tiff` preserves the embedded thumbnail.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Prepare test file
        test_tif = os.path.join(tmpdir, "compress_test.tif")
        shutil.copy2(CLEAN_TIFF, test_tif)

        # Add thumbnail
        add_thumbnail(test_tif)
        assert has_thumbnail(test_tif) is True

        # Run compression
        compress_tiff(test_tif)

        # Verify thumbnail is still present
        assert has_thumbnail(test_tif) is True, "Thumbnail missing after compression"

        # Verify structure explicitly
        with tifffile.TiffFile(test_tif) as tif:
            # Verify we still have subifds
            assert tif.pages[0].subifds, "SubIFDs missing after compression"
            # Verify compression is LZW (tag 259 = Compression)
            # LZW usually value 5
            assert (
                tif.pages[0].compression == 5
            ), f"Expected LZW(5), got {tif.pages[0].compression}"

            # Verify thumbnail compression if we set it?
            # We need to find the thumbnail series
            thumb_series = None
            thumb_offsets = set(tif.pages[0].subifds)
            for series in tif.series:
                if series.pages and series.pages[0].offset in thumb_offsets:
                    thumb_series = series
                    break

            assert thumb_series is not None, "Thumbnail series not found"
            # We also compressed thumbnail with LZW
            assert (
                thumb_series.pages[0].compression == 5
            ), "Thumbnail should also be compressed"
