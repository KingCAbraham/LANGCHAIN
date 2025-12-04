import sys
from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtCore import QPropertyAnimation
from gemini_client import GeminiOneShot, GeminiChatSession

class Load_ventana_modelos_basicos(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 1) Cargar UI
        uic.loadUi("interfaces/ventana_modelos.ui", self)

        # 2) Ajustes de ventana/menú (lo que ya tenías)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setWindowOpacity(1)
        self.boton_salir.clicked.connect(lambda: self.close())
        self.frame_superior.mouseMoveEvent = self.mover_ventana
        self.boton_menu.clicked.connect(self.mover_menu)
        self.boton_basico.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_basicos))
        self.boton_historial.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_historial))
        self.boton_chat.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_chat))

        # 3) Instancias Gemini para cada modo
        self.ai_basic = GeminiOneShot()                  # sin memoria
        self.ai_history = GeminiChatSession()            # memoria persistente
        self.ai_limited = GeminiChatSession(limit_turns=5)  # memoria con reinicio cada 5 preguntas

        # 4) Conectar widgets de cada página
        # Básico
        self.pushButton_6.clicked.connect(self._ask_basic)
        self.lineEdit.returnPressed.connect(self._ask_basic)
        self.textEdit.setReadOnly(True)

        # Historial
        self.pushButton_7.clicked.connect(self._ask_history)
        self.lineEdit_2.returnPressed.connect(self._ask_history)
        self.textEdit_2.setReadOnly(True)

        # Chat (memoria limitada)
        self.pushButton_8.clicked.connect(self._ask_limited)
        self.lineEdit_3.returnPressed.connect(self._ask_limited)
        self.textEdit_3.setReadOnly(True)

        self.show()

    # =====================
    #  Interacción con Gemini
    # =====================
    def _ask_basic(self):
        prompt = (self.lineEdit.text() or "").strip()
        if not prompt:
            return
        self._append_pair(self.textEdit, "Tú", prompt)
        self._set_waiting(self.pushButton_6, True)
        try:
            answer = self.ai_basic.ask(prompt)
            self._append_pair(self.textEdit, "Gemini", answer)
        except Exception as e:
            self._append_pair(self.textEdit, "Error", str(e))
        finally:
            self._set_waiting(self.pushButton_6, False)
            self.lineEdit.clear()

    def _ask_history(self):
        prompt = (self.lineEdit_2.text() or "").strip()
        if not prompt:
            return
        self._append_pair(self.textEdit_2, "Tú", prompt)
        self._set_waiting(self.pushButton_7, True)
        try:
            answer = self.ai_history.send(prompt)
            self._append_pair(self.textEdit_2, "Gemini", answer)
        except Exception as e:
            self._append_pair(self.textEdit_2, "Error", str(e))
        finally:
            self._set_waiting(self.pushButton_7, False)
            self.lineEdit_2.clear()

    def _ask_limited(self):
        """Chat con memoria que se reinicia cada 5 preguntas."""
        prompt = (self.lineEdit_3.text() or "").strip()
        if not prompt:
            return
        self._append_pair(self.textEdit_3, "Tú", prompt)
        self._set_waiting(self.pushButton_8, True)
        try:
            remaining = 5 - self.ai_limited.turns if self.ai_limited.turns < 5 else 0
            answer = self.ai_limited.send(prompt)
            self._append_pair(self.textEdit_3, "Gemini", answer)
            # Avisar cuando se reinició la memoria
            if self.ai_limited.turns == 1 and remaining == 0:
                self._append_pair(self.textEdit_3, "Sistema", "Memoria reiniciada (se cumplieron 5 interacciones).")
        except Exception as e:
            self._append_pair(self.textEdit_3, "Error", str(e))
        finally:
            self._set_waiting(self.pushButton_8, False)
            self.lineEdit_3.clear()

    # Helpers de UI
    def _append_pair(self, text_edit: QtWidgets.QTextEdit, speaker: str, text: str):
        html = f"<p><b>{speaker}:</b> {self._escape(text)}</p>"
        text_edit.append(html)
        text_edit.verticalScrollBar().setValue(text_edit.verticalScrollBar().maximum())

    def _escape(self, s: str) -> str:
        return QtGui.QTextDocument().toPlainText() if False else s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    def _set_waiting(self, button: QtWidgets.QPushButton, waiting: bool):
        button.setEnabled(not waiting)
        if waiting:
            button.setText("Pensando...")
        else:
            # Restituye el texto según el botón
            if button is self.pushButton_6:
                button.setText("Enviar")
            elif button is self.pushButton_7:
                button.setText("Enviar")
            elif button is self.pushButton_8:
                button.setText("Enviar")

    # =====================
    #  Lógica de ventana/menú (tuya)
    # =====================
    def mousePressEvent(self, event):
        self.clickPosition = event.globalPos()

    def mover_ventana(self, event):
        if not self.isMaximized():
            if event.buttons() == QtCore.Qt.LeftButton:
                self.move(self.pos() + event.globalPos() - self.clickPosition)
                self.clickPosition = event.globalPos()
                event.accept()
        if event.globalPos().y() <= 20:
            self.showMaximized()
        else:
            self.showNormal()

    def mover_menu(self):
        width = self.frame_lateral.width()
        normal = 0
        if width == 0:
            extender = 200
            self.boton_menu.setText("Menú")
        else:
            extender = normal
            self.boton_menu.setText("")
        self.animacion = QPropertyAnimation(self.frame_lateral, b"minimumWidth")
        self.animacion.setDuration(300)
        self.animacion.setStartValue(width)
        self.animacion.setEndValue(extender)
        self.animacion.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
        self.animacion.start()

        self.animacionb = QPropertyAnimation(self.boton_menu, b"minimumWidth")
        self.animacionb.setStartValue(width)
        self.animacionb.setEndValue(extender)
        self.animacionb.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
        self.animacionb.start()
