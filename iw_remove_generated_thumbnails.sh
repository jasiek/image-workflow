#!/bin/bash

echo "Removing generated thumbnail directories in subdirectories:"
find . -type d -name "thumbnails" -exec rm -rfv {} \;

echo "Removal complete."
