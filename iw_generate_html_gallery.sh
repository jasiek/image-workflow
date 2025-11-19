#!/bin/bash

# Get the directory where the script resides
SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/common.sh"

# Function to generate the HTML gallery
generate_gallery() {
    local file=$1
    # Skip thumbs themselves and converted files
    if [[ "$file" =~ thumbnails/ ]] || [[ "$file" == *converted* ]]; then
        return
    fi
    local base=$(basename "$file")
    local dir=$(dirname "$file")
    local thumb="$dir/thumbnails/${base%.*}-thumb.jpg"
    if [ -f "$thumb" ]; then
        echo "<div class='image-item'><a href='$file' target='_blank'><img src='$thumb' alt='$base'></a><p>$base</p></div>" >> gallery.html
    else
        echo "<div class='image-item'><a href='$file' target='_blank'><img src='$file' alt='$base' style='max-width:150px;'></a><p>$base</p></div>" >> gallery.html
    fi
}

# Create the gallery
cat > gallery.html << 'EOF'
<!DOCTYPE html>
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
EOF

echo "Generating HTML gallery using thumbnails..."
# Export the function
export -f generate_gallery
export SCRIPT_DIR

# Find all images and generate gallery entries
find . -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.tif" -o -iname "*.tiff" -o -iname "*.webp" \) -print0 | parallel --env SCRIPT_DIR -0 --no-notice 'source "$SCRIPT_DIR/common.sh"; generate_gallery {}'

# Close the HTML
echo "    </div></body></html>" >> gallery.html

echo "Gallery generated: gallery.html"
