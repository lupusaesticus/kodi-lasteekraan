#!/bin/bash

VERSION="1.1.0"

ROOT_PATH=$PWD
SRC_DIR="plugin.video.lasteekraan.err.ee"
ADDON_ID="plugin.video.lasteekraan.err.ee"
DIST_DIR="dist"
REPO_DIR="$ROOT_PATH/../repository.kodi.lupus/zips/$ADDON_ID"

echo "Cleaning old builds..."
rm -rf $DIST_DIR
mkdir -p $DIST_DIR/$ADDON_ID

echo "Copying core files from $SRC_DIR..."
cp $SRC_DIR/addon.xml $SRC_DIR/lasteekraan_addon.py $DIST_DIR/$ADDON_ID/

echo "Copying resources..."
cp -r $SRC_DIR/resources $DIST_DIR/$ADDON_ID/

# Remove any python cache files that might have been copied
find $DIST_DIR -name "__pycache__" -type d -exec rm -rf {} +

echo "Creating ZIP package..."
cd $DIST_DIR

# Create the zip for GitHub Release
zip -r "$ROOT_PATH/${ADDON_ID}.zip" "$ADDON_ID"

echo "Updating Repo Store..."
mkdir -p "$REPO_DIR"
# Copy the addon.xml to the repo destination
cp "$ADDON_ID/addon.xml" "$REPO_DIR/"
# Create the versioned ZIP for the Kodi Repo
zip -r "$REPO_DIR/${ADDON_ID}-${VERSION}.zip" "$ADDON_ID"

# Cleanup
cd "$ROOT_PATH"
rm -rf $DIST_DIR

echo "------------------------------------------------"
echo "Build complete: ${ADDON_ID}-${VERSION}.zip"
echo "------------------------------------------------"