@echo off
title Publish Stand by Me Doraemon 3D CGI to YouTube Studio
color 0b

echo ==============================================================================
echo        NITESH 3D CGI STUDIOS - 1-CLICK YOUTUBE UPLOADER & MONETIZATION
echo ==============================================================================
echo.
echo [1/3] Copying 100%% Monetization-Safe SEO Title, Description & Tags to Clipboard...
"C:\Users\SVNITHESHPC\Downloads\Jarvis\venv\Scripts\python.exe" "C:\Users\SVNITHESHPC\Desktop\Jarvis_Studios\copy_doraemon_metadata_to_clipboard.py"
echo.
echo [2/3] Launching YouTube Studio Upload Dashboard in your Browser...
start "" "https://studio.youtube.com/channel/UC/videos/upload?d=pt"
timeout /t 2 /nobreak >nul
echo.
echo [3/3] Opening Windows File Explorer with your 3D Master Video Selected...
explorer /select,"C:\Users\SVNITHESHPC\Desktop\Jarvis_Studios\doraemon_3dcg_shorts_master.mp4"
echo.
echo ==============================================================================
echo [READY] Simply Drag and Drop 'doraemon_3dcg_shorts_master.mp4' into your browser!
echo Then press Ctrl+V to paste the Title, Description, and Tags!
echo ==============================================================================
pause
