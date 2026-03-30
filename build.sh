#!/bin/bash

ADDON_ID="plugin.video.lasteekraan.err.ee"
VERSION="1.0.0"
DIST_DIR="dist"

echo "Cleaning old builds..."
rm -rf $DIST_DIR
mkdir -p $DIST_DIR/$ADDON_ID

echo "Copying core files..."
cp addon.xml default.py lasteekraan_addon.py $DIST_DIR/$ADDON_ID/

echo "Copying resources..."
# This copies the entire resources folder (including lib/ and language/)
cp -r resources $DIST_DIR/$ADDON_ID/

# Remove any python cache files that might have been copied
find $DIST_DIR -name "__pycache__" -type d -exec rm -rf {} +

echo "Creating ZIP package..."
cd $DIST_DIR
zip -r ../${ADDON_ID}-${VERSION}.zip $ADDON_ID
cd ..

echo "------------------------------------------------"
echo "Build complete: ${ADDON_ID}-${VERSION}.zip"
echo "------------------------------------------------"