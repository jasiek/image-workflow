import os
import shutil
import tempfile
import pytest
from image_workflow.generate_html_gallery import (
    main as generate_gallery_main,
    generate_gallery_item,
)
from image_workflow.common import add_thumbnail, extract_thumbnail

TEST_IMAGE_DIR = "test_images"
CLEAN_TIFF = os.path.join(TEST_IMAGE_DIR, "clean_sample.tif")


def test_gallery_generation():
    """
    Simulate workflow:
    1. Create temp dir with images
    2. Add thumbnails
    3. Extract thumbnails
    4. Generate Gallery
    5. Verify gallery.html content
    """
    # We need to execute this in a temp dir because generate_html_gallery uses iterate_images which uses Path(".").rglob
    # So we must chdir.

    original_cwd = os.getcwd()

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            os.chdir(tmpdir)

            # Setup
            shutil.copy2(os.path.join(original_cwd, CLEAN_TIFF), "test.tif")

            # 1. Add thumbnail
            add_thumbnail("test.tif")

            # 2. Extract thumbnail (mimic extract_thumbnails.py behavior)
            thumb_dir = "thumbnails"
            if not os.path.exists(thumb_dir):
                os.makedirs(thumb_dir)
            extract_thumbnail("test.tif", thumb_dir)

            assert os.path.exists("thumbnails/test.tif.jpg")

            # 3. Generate gallery
            # This prints to stdout and writes gallery.html
            # But generate_gallery.py main() calls iterate_images with collect_results=True
            # which currently fails because common.py doesn't support it.

            try:
                generate_gallery_main()
            except TypeError as e:
                pytest.fail(
                    f"generate_html_gallery failed with TypeError (likely iterate_images mismatch): {e}"
                )

            assert os.path.exists("gallery.html")

            content = open("gallery.html").read()

            # Verify content
            # Should link to the thumbnail
            # Current generate_gallery expects thumbnails/test-thumb.jpg in subdir?
            # Or whatever structure.

            # Checks:
            assert "test.tif" in content
            # It should point to the thumbnail image
            # If it fails to find it, it points to test.tif

            # It must link to the thumbnail if it exists
            if "src='thumbnails/test.tif.jpg'" not in content:
                pytest.fail(
                    "Gallery did not link to the extracted thumbnail 'thumbnails/test.tif.jpg'"
                )

        finally:
            os.chdir(original_cwd)
