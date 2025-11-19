#!/bin/bash

# Get the directory where the script resides
SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/common.sh"

# Function to extract thumbnail if present
extract_thumbnail() {
    local file=$1
    local ext="${file##*.}"
    local thumb="${file%.*}_thumb.${ext}"
    if has_thumbnail "$file"; then
        echo "Extracting thumbnail from $file to $thumb"
        exiv2 -et "$file"
        # exiv2 -et extracts to <file>-thumb.jpg
        local extracted_thumb="${file}-thumb.jpg"
        if [ -f "$extracted_thumb" ]; then
            mv "$extracted_thumb" "$thumb"
            echo "Extracted to $thumb"
        else
            echo "Failed to extract thumbnail for $file"
        fi
    else
        echo "No thumbnail in $file"
    fi
}

iterate_images extract_thumbnail
