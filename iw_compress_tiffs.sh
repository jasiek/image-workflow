#!/bin/bash

# Get the directory where the script resides
SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/common.sh"

# Function to compress a TIFF image with ZIP compression
compress_tiff() {
    local file=$1
    echo "Compressing $file with ZIP algorithm"
    gm convert -compress zip "$file" "${file}_tmp" 2>/dev/null
    if [ $? -eq 0 ] && [ -f "${file}_tmp" ]; then
        mv "${file}_tmp" "$file"
        echo "Compressed $file"
    else
        echo "Failed to compress $file"
        rm -f "${file}_tmp"  # Clean up temp if failed
    fi
}

iterate_images compress_tiff "*.tif" "*.tiff"
