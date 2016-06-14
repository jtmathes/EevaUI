#! /bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR; cd ..; echo $PWD

# Installs & utilizes the xcode developer environment.
#echo Using Xcode…
#xcode-select —-install

# Installs pip to install pyinstaller & sip.
hash pip 2>/dev/null && echo Found: pip || { echo Installing pip…; sudo easy_install pip; }

# Installs pyinstaller to use script.
hash pyinstaller 2>/dev/null && echo Found: PyInstaller || { echo Installing pyinstaller…; sudo pip install pyinstaller; }

# Installs Homebrew to install SIP
hash brew 2>/dev/null && echo Found: Homebrew|| { echo Installing Homebrew…; /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"; }

# Installs sip so the rthook_pyqt4 can import it.
# SIP binds Python to C++
hash sip 2>/dev/null && echo Found: SIP || { echo Installing SIP…; brew install sip; }

# Script.
echo Making EEVA GUI application…
pyinstaller --runtime-hook rthook_pyqt4.py eeva_ui.py --windowed --onefile --icon resources/NERLogo.icns