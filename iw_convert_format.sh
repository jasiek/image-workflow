#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 <target_format>"
    echo "Example: $0 png"
    exit 1
fi

TARGET_FORMAT=$1

# Get the directory where the script resides
SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/common.sh"

# Function to convert an image to the target format and place in mirrored hierarchy
convert_to_format() {
    local file=$1
    # Skip files already in converted directory
    if [[ "$file" == *converted* ]]; then
        return
    fi
    local base=$(basename "$file" .${file##*.})
    local dir=$(dirname "$file")
    local converted_dir="converted$dir"
    mkdir -p "$converted_dir"
    local new_file="$converted_dir/${base}.$TARGET_FORMAT"
    echo "Converting $file to $new_file"
    gm convert "$file" "$new_file" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "Converted to $TARGET_FORMAT: $new_file"
    else
        echo "Failed to convert $file"
    fi
}

# Export the function and variable for parallel processing
export -f convert_to_format
export TARGET_FORMAT

echo "Converting all images to .$TARGET_FORMAT format in converted/ directory"
iterate_images convert_to_format "*.jpg" "*.jpeg" "*.png" "*.tif" "*.tiff" "*.webp"
