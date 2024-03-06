from PyQt5 import QtWidgets, QtCore

class AppDelegate(QtWidgets.QApplication):
    @classmethod
    def applicationSupportsSecureRestorableState(cls):
        return True