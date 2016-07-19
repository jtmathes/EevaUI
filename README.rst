Run from source:

 - Install Python 2.7, if you already have python installed make a note of which version (32 vs 64 bit) you have installed and make sure to download the same version of the dependencies below.  If you're not sure which python version you have you can tell from one of the top two answers here http://stackoverflow.com/questions/1405913/how-do-i-determine-if-my-python-shell-is-executing-in-32bit-or-64bit-mode-on-os.
 - Install PyQt4.  If using windows then it's easiest to use one of the installers.  Make sure to choose the one for python 2.7 and match which version of python you have.  https://riverbankcomputing.com/software/pyqt/download 
 - Install PySerial 
 - Run "eeva_ui.py" which should launch the main window.
 - If you want to build an executable then for windows run /pyinstaller/eeva_windows.bat.   If it complains that you don't have permission then try running the command shell as Administrator or just try running it two or three times.  
 
