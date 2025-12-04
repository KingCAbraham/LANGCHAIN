from PyQt5 import QtWidgets, uic
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox

# Importa tus diálogos
try:
    from load.load_ventana_modelos_basicos import Load_ventana_modelos_basicos
except Exception as e:
    Load_ventana_modelos_basicos = None
    _err_basicos = e

try:
    from load.load_ventana_langchain import Load_ventana_langchain
except Exception as e:
    Load_ventana_langchain = None
    _err_langchain = e

class Load_ventana_menu(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("interfaces/ventana_menu.ui", self)
        self.showMaximized()

        # Conexiones de menú
        if hasattr(self, "actionBasicos"):
            self.actionBasicos.triggered.connect(self.abrirVentanaBasicos)
        if hasattr(self, "actionLangChain"):
            self.actionLangChain.triggered.connect(self.abrirVentanaLangChain)
        if hasattr(self, "actionsalir"):
            self.actionsalir.triggered.connect(self.cerrarVentana)

    def abrirVentanaBasicos(self):
        if Load_ventana_modelos_basicos is None:
            QMessageBox.critical(self, "Error", f"No se pudo cargar 'Modelos básicos':\n{_err_basicos}")
            return
        dlg = Load_ventana_modelos_basicos(self)
        dlg.setWindowModality(QtCore.Qt.ApplicationModal)
        dlg.exec_()

    def abrirVentanaLangChain(self):
        if Load_ventana_langchain is None:
            QMessageBox.critical(self, "Error", f"No se pudo cargar 'LangChain':\n{_err_langchain}")
            return
        dlg = Load_ventana_langchain(self)
        dlg.setWindowModality(QtCore.Qt.ApplicationModal)
        dlg.exec_()

    def cerrarVentana(self):
        self.close()
