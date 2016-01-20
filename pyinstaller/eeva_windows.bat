
cd ..

pyinstaller eeva_ui.py  ^
--windowed ^
--onefile ^
--icon=./resources/NERLogo.ico

cd ./pyinstaller

pause