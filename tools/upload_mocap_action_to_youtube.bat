@echo off
title NITESH CGI STUDIOS - FULL-MOVEMENT MOCAP PUBLISHER
echo ================================================================================
echo   NITESH CGI STUDIOS // FULL-MOVEMENT MOCAP YOUTUBE PUBLISHER
echo ================================================================================
echo.
echo [1] Copying High-Retention Title, Description and Pinned Comment...
"C:\Users\SVNITHESHPC\Downloads\Jarvis\venv\Scripts\python.exe" "C:\Users\SVNITHESHPC\Desktop\Jarvis_Studios\copy_mocap_metadata_to_clipboard.py"
echo.
echo [2] Opening YouTube Studio Upload in your Default Browser...
start "" "https://studio.youtube.com/channel/UC/videos/upload?d=ud"
echo.
echo [3] Opening File Explorer with Full-Movement 60 FPS video pre-selected...
explorer.exe /select,"C:\Users\SVNITHESHPC\Desktop\Jarvis_Studios\protocol_shiva_mocap_action_short.mp4"
echo.
echo --------------------------------------------------------------------------------
echo SUCCESS!
echo - Drag and drop protocol_shiva_mocap_action_short.mp4 into YouTube Studio.
echo - Paste (Ctrl+V) the Title and Description into YouTube Studio.
echo ================================================================================
pause
