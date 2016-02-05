
# Update python code to match designer file.
import subprocess
process = subprocess.Popen('pyrcc4 ./resources/images.qrc -o images_qr.py', shell=True, stdout=subprocess.PIPE)
process.wait()
process = subprocess.Popen('pyuic4 eeva_designer.ui -o eeva_designer.py', shell=True, stdout=subprocess.PIPE)
process.wait()
print process.returncode