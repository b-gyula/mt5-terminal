#!/bin/bash

# Only install if not already present
if [ ! -f "/opt/wineprefix/drive_c/Metatrader-5/terminal64.exe" ]; then
    echo "MetaTrader 5 not found. Starting installation..."

    # MetaTrader download url
    URL="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"
    # WebView2 Runtime download url
    URL_WEBVIEW="https://msedge.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/c1336fd6-a2eb-4669-9b03-949fc70ace0e/MicrosoftEdgeWebview2Setup.exe"

    # Download
    wget -q $URL
    wget -q $URL_WEBVIEW

    # Set environment to Windows 10
    winecfg -v=win10

    # Install WebView2
    wine MicrosoftEdgeWebview2Setup.exe /silent /install
    wineserver -w

    # Install MT5
    wine mt5setup.exe /auto /path:"C:\Metatrader-5"
    wineserver -w

    # Clean up
    rm mt5setup.exe MicrosoftEdgeWebview2Setup.exe
else
    echo "MetaTrader 5 already installed."
fi

# Run MT5 (Skip if in BUILD_MODE)
if [ "$BUILD_MODE" = "1" ]; then
    echo "Metatrader 5 installed successfully (Build Mode). Skipping launch."
    exit 0
fi

# Run MT5
echo "Launching MetaTrader 5..."
wine /opt/wineprefix/drive_c/Metatrader-5/terminal64.exe /portable