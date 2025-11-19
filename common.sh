#!/bin/bash

# Function to check if image has embedded thumbnail
has_thumbnail() {
    local file=$1
    local size=$(exiv2 -pp "$file" 2>/dev/null | wc -c)
    if [ "$size" -gt 0 ]; then
        return 0  # true
    else
        return 1  # false
    fi
}

# Function to add a thumbnail to an image
add_thumbnail() {
    local file=$1
    local thumb="${file%.*}-thumb.jpg"  # Thumbnail file name required by exiv2
    # Generate a small thumbnail image
    gm convert "$file" -resize 150x150 "$thumb" 2>/dev/null
    if [ -f "$thumb" ]; then
        # Embed the thumbnail into the image metadata
        exiv2 -i t "$file" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "Added thumbnail to $file"
        else
            echo "Failed to embed thumbnail for $file"
        fi
        # Clean up the temporary thumbnail file
        rm "$thumb"
    else
        echo "Failed to generate thumbnail for $file"
    fi
}

# Function to iterate over all image files in subdirectories
iterate_images() {
    local func_name=$1
    # Supported image extensions
    local extensions=("*.jpg" "*.jpeg" "*.png" "*.tif" "*.tiff" "*.webp")

    echo "Iterating over image files in subdirectories:"

    # Loop through each extension and find files recursively
    for ext in "${extensions[@]}"; do
        find . -type f -iname "$ext" 2>/dev/null | while read -r file; do
            echo "Processing $file"
            "$func_name" "$file"
        done
    done
}
