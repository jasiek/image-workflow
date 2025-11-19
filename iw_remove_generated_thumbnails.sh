#!/bin/bash

echo "Removing generated thumbnail files (*-thumb.*) in subdirectories:"
find . -type f -name "*-thumb.*" -exec rm -v {} \;

echo "Removal complete."
