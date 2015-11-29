
import os
import sys
from eeva_main_window import EevaMainWindow
from eeva_controller import EevaController
from connection_controller import ConnectionController
from glob_link import GlobLink
from PyQt4 import QtGui

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    app.setStyle('plastique')
    app.setWindowIcon(QtGui.QIcon('./resources/NERLogoTransparent.png'))
    
    if os.name == 'nt':
        # If running on windows then need to unassociate process from python so that
        # the OS will show the correct icon in the taskbar.
        import ctypes
        myappid = u'ner.eeva.ui.1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    # Configure system
    link = GlobLink()
    controller = EevaController(link)
    connection_controller = ConnectionController(controller, link)
    window = EevaMainWindow(app, controller, connection_controller)
    controller.set_view(window)
    connection_controller.set_view(window)
    connection_controller.start_link_timer()
    
    window.show()

    sys.exit(app.exec_())