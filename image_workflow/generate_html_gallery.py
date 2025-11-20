from pathlib import Path
from .common import iterate_images


HTML_HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Gallery</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; padding: 20px; }
        .gallery { display: flex; flex-wrap: wrap; gap: 20px; }
        .image-item { display: flex; flex-direction: column; align-items: center; background: white; padding: 10px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .image-item img { max-width: 150px; max-height: 150px; cursor: pointer; }
        .image-item p { margin: 5px 0; font-size: 12px; }
    </style>
</head>
<body>
    <h1>Image Gallery</h1>
    <div class="gallery">
"""

HTML_FOOTER = """    </div>
</body>
</html>
"""


def generate_gallery_item(file_path):
    file_path = Path(file_path)
    # Skip thumbnail files themselves if they are picked up
    if "thumbnails" in file_path.parts or "converted" in file_path.parts:
        return None
    base = file_path.name

    # Check for extracted thumbnail in root thumbnails/ directory
    # Matches naming convention from extract_thumbnails.py: filename.ext.jpg
    thumb_flat = Path("thumbnails") / f"{file_path.name}.jpg"

    if thumb_flat.exists():
        img_src = str(thumb_flat)
    else:
        # Fallback to sidecar in same dir check (legacy)
        # or just link to original
        img_src = str(file_path)

    return f"""<div class='image-item'><a href='{file_path}' target='_blank'><img src='{img_src}' alt='{base}'></a><p>{base}</p></div>"""


def main():
    extensions = [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"]
    items = iterate_images(generate_gallery_item, extensions, collect_results=True)
    with open("gallery.html", "w") as f:
        f.write(HTML_HEADER)
        f.write("\n".join(items))
        f.write(HTML_FOOTER)
    print("Gallery generated: gallery.html")


if __name__ == "__main__":
    main()
