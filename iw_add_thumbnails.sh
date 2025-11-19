#!/bin/bash

# Get the directory where the script resides
SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/common.sh"

# Function to add thumbnail if not present
add_thumbnails_if_needed() {
    local file=$1
    if ! has_thumbnail "$file"; then
        add_thumbnail "$file"
    else
        echo "Already has thumbnail"
    fi
}

# Export the function for parallel processing
export -f add_thumbnails_if_needed

iterate_images add_thumbnails_if_needed "*.jpg" "*.jpeg" "*.png" "*.tif" "*.tiff" "*.webp"
