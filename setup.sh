#!/bin/bash

# Ensure Python requirements are installed
echo "Installing Python requirements..."
pip install --user -r requirements.txt

# Check if Chrome is already extracted
CHROME_PATH="chrome-extracted/opt/google/chrome/google-chrome"
if [ ! -f "$CHROME_PATH" ]; then
    echo "Google Chrome not found in chrome-extracted. Downloading and extracting..."
    if wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb; then
        echo "Download successful. Extracting..."
        dpkg -x /tmp/google-chrome.deb chrome-extracted
        rm /tmp/google-chrome.deb
        echo "Google Chrome extracted successfully."
    else
        echo "Failed to download Google Chrome."
        exit 1
    fi
else
    echo "Google Chrome is already extracted. Skipping download."
fi
