import os
import pytest
from image_workflow.common import (
    has_thumbnail,
    add_thumbnail,
    extract_thumbnail,
    remove_thumbnail,
    PngImageProcessor,
    ExifImageProcessor,
)


def test_has_thumbnail():
    """Test that has_thumbnail returns False for clean sample images."""
    test_dir = "test_images"
    files = [
        os.path.join(test_dir, f)
        for f in os.listdir(test_dir)
        if f.endswith((".jpg", ".jpeg", ".tif", ".tiff", ".png"))
    ]
    for file_path in files:
        assert not has_thumbnail(file_path), f"{file_path} should not have thumbnail"

    # Test non-existent file
    assert not has_thumbnail("nonexistent.jpg"), "Non-existent file should return False"


def test_add_thumbnail():
    """Test adding thumbnails to copies of test images."""
    import shutil
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # Test PNG
        png_src = "test_images/clean_sample.png"
        png_dst = os.path.join(tmpdir, "test.png")
        shutil.copy2(png_src, png_dst)
        assert not PngImageProcessor.has_thumbnail(png_dst)
        assert add_thumbnail(png_dst)
        assert PngImageProcessor.has_thumbnail(png_dst)
        # Extract to another dir
        extract_dir = os.path.join(tmpdir, "thumbs")
        os.makedirs(extract_dir)
        assert extract_thumbnail(png_dst, extract_dir)
        assert os.path.exists(os.path.join(extract_dir, "test.png.jpg"))
        # Remove
        assert remove_thumbnail(png_dst)
        assert not PngImageProcessor.has_thumbnail(png_dst)

        # Test unsupported
        with pytest.raises(ValueError):
            add_thumbnail("unsupported.xyz")


def test_processor_methods_on_nonexistent():
    """Test processor methods handle nonexistent files gracefully."""
    assert not ExifImageProcessor.has_thumbnail("nonexistent.jpg")
    assert not ExifImageProcessor.add_thumbnail("nonexistent.jpg")
    assert not ExifImageProcessor.extract_thumbnail("nonexistent.jpg", "thumbs")
    assert not ExifImageProcessor.remove_thumbnail("nonexistent.jpg")

    assert not PngImageProcessor.has_thumbnail("nonexistent.png")
    assert not PngImageProcessor.add_thumbnail("nonexistent.png")
    assert not PngImageProcessor.extract_thumbnail("nonexistent.png", "thumbs")
    assert not PngImageProcessor.remove_thumbnail("nonexistent.png")
