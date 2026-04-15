#!/bin/bash
# Copyright 2000-2026, MetaQuotes Ltd.

# Only install if not already present
if [ -f "$MT5_PATH" ]; then
     echo "MetaTrader 5 already installed."
	  exit 1
fi

# MetaTrader and WebView2 download urls
URL_MT5="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"
URL_WEBVIEW="https://msedge.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/f2910a1e-e5a6-4f17-b52d-7faf525d17f8/MicrosoftEdgeWebview2Setup.exe"

echo Download MetaTrader and WebView2 runtime
# Use -L to follow redirects, -f to fail on HTTP errors, -A for user-agent
[ ! -f ~/mt5setup.exe ] && curl -L -f  "$URL_MT5" --output ~/mt5setup.exe
[ ! -f ~/MicrosoftEdgeWebview2Setup.exe ] && curl -L -f  "$URL_WEBVIEW" --output ~/MicrosoftEdgeWebview2Setup.exe

if [ ! -f "$WINEPREFIX" ]; then
	echo Init wine prefix !!! Open VNC to install mono !!!
	wineboot -i
	echo Set environment to Windows 11
	winecfg /v win11
fi

echo Install WebView2 runtime
wine MicrosoftEdgeWebview2Setup.exe /silent /install
#wineserver -w

echo Install MetaTrader 5
wine mt5setup.exe /auto /path:"C:\mt5"
#wineserver -w
#echo Please reboot OS
