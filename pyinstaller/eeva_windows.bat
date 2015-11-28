
cd ..

pyinstaller eeva_ui.py  ^
--hidden-import=scipy.linalg ^
--hidden-import=scipy.linalg.cython_blas ^
--hidden-import=scipy.linalg.cython_lapack ^
--hidden-import=scipy.integrate ^
--windowed ^
--onefile ^
--icon=./resources/NERLogo.ico

pause