
cd ..

pyinstaller eeva_ui.py  ^
--runtime-hook rthook_pyqt4.py ^
--windowed ^
--onefile ^
--icon=./resources/NERLogo.ico

cd ./pyinstaller

pause