
import sys
from eeva_main_window import EevaMainWindow
from eeva_controller import EevaController
from glob_link import GlobLink
from PyQt4 import QtGui

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    app.setStyle('plastique')
    
    # Configure system
    link = GlobLink()
    controller = EevaController(link)
    window = EevaMainWindow(app, controller)
    controller.set_view(window)
    
    window.show()

    sys.exit(app.exec_())