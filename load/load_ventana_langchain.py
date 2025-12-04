# load/load_ventana_langchain.py
from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtCore import QPropertyAnimation, QThread, pyqtSignal
import html, os, shutil, re

# Desactivar frameworks pesados (por si LangChain los quisiera usar)
os.environ["USE_TORCH"] = "0"
os.environ["USE_TF"] = "0"

# Base del proyecto (carpeta raíz que contiene main.py)
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# ==== Importamos directamente las funciones de los ejercicios ====
from ejercicios.ej1_llmchain import run_llmchain
from ejercicios.ej2_sequential import run_sequential
from ejercicios.ej3_simple_sequential import run_simple_sequential
from ejercicios.ej4_parseo import run_ej4
from ejercicios.ej5_varios_pasos import run_ej5
from ejercicios.ej6_memoria import run_ej6
from ejercicios.ej7_persistencia import run_ej7
from ejercicios.ej8_rag import run_ej8


# =========================
# Worker en hilo
# =========================
class TaskWorker(QThread):
    done = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn, self.args, self.kwargs = fn, args, kwargs

    def run(self):
        try:
            out = self.fn(*self.args, **self.kwargs)
            self.done.emit(out if isinstance(out, str) else str(out))
        except Exception as e:
            self.failed.emit(str(e))


# =========================
# VENTANA LANGCHAIN
# =========================
class Load_ventana_langchain(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(BASE, "interfaces", "ventana_langchain.ui"), self)

        # Estética (sombras suaves)
        self._add_shadow(self.frame_paginas, radius=24, y=10, alpha=60)
        self._add_shadow(self.frame_lateral, radius=18, y=6, alpha=50)

        # ----- cromo -----
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setWindowOpacity(1)
        self.boton_salir.clicked.connect(self.close)
        self.frame_superior.mouseMoveEvent = self._mover_ventana
        self.boton_menu.clicked.connect(self._mover_menu)

        # ----- navegación lateral -> páginas -----
        self.boton_ej1.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_basicos))
        self.boton_ej2.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_historial))
        self.boton_ej3.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_chat))
        self.boton_ej4.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_4))
        self.boton_ej5.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_5))
        self.boton_ej6.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_6))
        self.boton_ej7.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_7))
        self.boton_ej8.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.page_8))

        # Guardar texto original de los botones para restaurarlo
        self._setup_button_labels()

        # ----- Conexiones por ejercicio -----
        # Ej1: 2 entradas (lineEdit, lineEdit_9)
        self.pushButton_6.clicked.connect(self._on_ej1)
        self.lineEdit.returnPressed.connect(self._on_ej1)
        self.lineEdit_9.returnPressed.connect(self._on_ej1)
        self.textEdit.setReadOnly(True)

        # Ej2: 2 entradas (lineEdit_11, lineEdit_2)
        self.pushButton_7.clicked.connect(self._on_ej2)
        self.lineEdit_11.returnPressed.connect(self._on_ej2)
        self.lineEdit_2.returnPressed.connect(self._on_ej2)
        self.textEdit_2.setReadOnly(True)

        # Ej3: 2 entradas (lineEdit_12, lineEdit_3)
        self.pushButton_8.clicked.connect(self._on_ej3)
        self.lineEdit_12.returnPressed.connect(self._on_ej3)
        self.lineEdit_3.returnPressed.connect(self._on_ej3)
        self.textEdit_3.setReadOnly(True)

        # Ej4: 2 entradas (lineEdit_10, lineEdit_4)
        self.pushButton_9.clicked.connect(self._on_ej4)
        self.lineEdit_10.returnPressed.connect(self._on_ej4)
        self.lineEdit_4.returnPressed.connect(self._on_ej4)
        self.textEdit_4.setReadOnly(True)

        # Ej5: 2 entradas (lineEdit_13, lineEdit_5)
        self.pushButton_10.clicked.connect(self._on_ej5)
        self.lineEdit_13.returnPressed.connect(self._on_ej5)
        self.lineEdit_5.returnPressed.connect(self._on_ej5)
        self.textEdit_5.setReadOnly(True)

        # Ej6: 1 entrada (lineEdit_6)
        self.pushButton_11.clicked.connect(self._on_ej6)
        self.lineEdit_6.returnPressed.connect(self._on_ej6)
        self.textEdit_6.setReadOnly(True)

        # Ej7: 1 entrada (lineEdit_7)
        self.pushButton_12.clicked.connect(self._on_ej7)
        self.lineEdit_7.returnPressed.connect(self._on_ej7)
        self.textEdit_7.setReadOnly(True)

        # Ej8: 1 entrada + botón para cargar PDF
        self.pushButton_13.clicked.connect(self._on_ej8)
        self.lineEdit_8.returnPressed.connect(self._on_ej8)
        if hasattr(self, "cargar_archiv"):
            self.cargar_archiv.clicked.connect(self._seleccionar_pdf)
        self.textEdit_8.setReadOnly(True)

        self._workers = []
        self._ej8_pdf_path = None
        self.show()

    # ---------- Helpers de UI ----------
    def _setup_button_labels(self):
        self._buttons = []
        for name in [
            "pushButton_6", "pushButton_7", "pushButton_8", "pushButton_9",
            "pushButton_10", "pushButton_11", "pushButton_12", "pushButton_13"
        ]:
            btn = getattr(self, name, None)
            if isinstance(btn, QtWidgets.QPushButton):
                btn._original_text = btn.text()
                self._buttons.append(btn)

    # Soporta dos cajitas o un solo texto con formato [Contexto]...[Instrucción]...
    def _split_ctx_inst(self, ctx_text: str, inst_text: str):
        ctx = (ctx_text or "").strip()
        inst = (inst_text or "").strip()
        # Fallback: patrón [Contexto]... [Instrucción]...
        if not inst and re.search(r"\[contexto\]", ctx, re.I) and re.search(r"\[instrucci[oó]n\]", ctx, re.I):
            m = re.search(r"\[contexto\](.*?)\[instrucci[oó]n\](.*)$", ctx, re.I | re.S)
            if m:
                ctx = m.group(1).strip()
                inst = m.group(2).strip()
        return ctx, inst

    # ---------- Acciones por ejercicio ----------
    def _on_ej1(self):
        ctx, inst = self._split_ctx_inst(self.lineEdit.text(), self.lineEdit_9.text())
        if not ctx or not inst:
            return
        self._run_two_inputs(self.textEdit, self.pushButton_6, self.lineEdit, self.lineEdit_9, run_llmchain, ctx, inst)

    def _on_ej2(self):
        ctx, inst = self._split_ctx_inst(self.lineEdit_11.text(), self.lineEdit_2.text())
        if not ctx or not inst:
            return
        self._run_two_inputs(self.textEdit_2, self.pushButton_7, self.lineEdit_11, self.lineEdit_2, run_sequential, ctx, inst)

    def _on_ej3(self):
        ctx, inst = self._split_ctx_inst(self.lineEdit_12.text(), self.lineEdit_3.text())
        if not ctx or not inst:
            return
        self._run_two_inputs(self.textEdit_3, self.pushButton_8, self.lineEdit_12, self.lineEdit_3, run_simple_sequential, ctx, inst)

    def _on_ej4(self):
        ctx, inst = self._split_ctx_inst(self.lineEdit_10.text(), self.lineEdit_4.text())
        if not ctx or not inst:
            return
        self._run_two_inputs(self.textEdit_4, self.pushButton_9, self.lineEdit_10, self.lineEdit_4, run_ej4, ctx, inst)

    def _on_ej5(self):
        ctx, inst = self._split_ctx_inst(self.lineEdit_13.text(), self.lineEdit_5.text())
        if not ctx or not inst:
            return
        self._run_two_inputs(self.textEdit_5, self.pushButton_10, self.lineEdit_13, self.lineEdit_5, run_ej5, ctx, inst)

    def _on_ej6(self):
        texto = (self.lineEdit_6.text() or "").strip()
        if not texto:
            return
        self._run_one_input(self.textEdit_6, self.pushButton_11, self.lineEdit_6, run_ej6, texto)

    def _on_ej7(self):
        texto = (self.lineEdit_7.text() or "").strip()
        if not texto:
            return
        self._run_one_input(self.textEdit_7, self.pushButton_12, self.lineEdit_7, run_ej7, texto)

    def _seleccionar_pdf(self):
        dest_dir = os.path.join(BASE, "documentos")
        os.makedirs(dest_dir, exist_ok=True)
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Selecciona un PDF", dest_dir, "PDF (*.pdf)")
        if not fname:
            return
        dest_path = os.path.join(dest_dir, os.path.basename(fname))
        try:
            if os.path.abspath(fname) != os.path.abspath(dest_path):
                shutil.copy2(fname, dest_path)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Ejercicio 8", f"No pude copiar el archivo:\n{e}")
            return
        self._ej8_pdf_path = dest_path
        self._append(self.textEdit_8, "Sistema", f"Documento cargado: {os.path.basename(dest_path)}")

    def _on_ej8(self):
        pregunta = (self.lineEdit_8.text() or "").strip()
        if not pregunta:
            return
        if not self._ej8_pdf_path or not os.path.exists(self._ej8_pdf_path):
            self._seleccionar_pdf()
            if not self._ej8_pdf_path:
                QtWidgets.QMessageBox.information(self, "Ejercicio 8", "Debes elegir un PDF para poder preguntar.")
                return
        self._append(self.textEdit_8, "Tú", pregunta)
        self._set_wait(self.pushButton_13, True)
        w = TaskWorker(run_ej8, pregunta, self._ej8_pdf_path)
        w.done.connect(lambda t: self._on_done(self.textEdit_8, self.pushButton_13, self.lineEdit_8, t))
        w.failed.connect(lambda e: self._on_err(self.textEdit_8, self.pushButton_13, e))
        self._start(w)

    # ---------- helpers de ejecución ----------
    def _run_two_inputs(self, te, btn, line_a, line_b, fn, a, b):
        # Aquí quitamos [Contexto]/[Instrucción] y usamos Prompt 1 / Prompt 2
        self._append(te, "Tú", f"Prompt 1: {a}\nPrompt 2: {b}")
        self._set_wait(btn, True)
        w = TaskWorker(fn, a, b)
        w.done.connect(lambda t: self._on_done(te, btn, None, t))
        w.failed.connect(lambda e: self._on_err(te, btn, e))
        self._start(w)
        if line_a:
            line_a.clear()
        if line_b:
            line_b.clear()

    def _run_one_input(self, te, btn, line, fn, txt):
        self._append(te, "Tú", txt)
        self._set_wait(btn, True)
        w = TaskWorker(fn, txt)
        w.done.connect(lambda t: self._on_done(te, btn, line, t))
        w.failed.connect(lambda e: self._on_err(te, btn, e))
        self._start(w)

    def _add_shadow(self, widget, radius=24, y=8, alpha=70):
        effect = QtWidgets.QGraphicsDropShadowEffect(self)
        effect.setBlurRadius(radius)
        effect.setOffset(0, y)
        effect.setColor(QtGui.QColor(0, 0, 0, alpha))
        widget.setGraphicsEffect(effect)

    def _start(self, w):
        if not hasattr(self, "_workers"):
            self._workers = []
        self._workers.append(w)
        w.finished.connect(lambda: self._workers.remove(w))
        w.start()

    def _on_done(self, te, btn, line, txt):
        self._append(te, "Modelo", txt)
        self._set_wait(btn, False)
        if line:
            line.clear()

    def _on_err(self, te, btn, err):
        self._append(te, "Error", err)
        self._set_wait(btn, False)

    def _append(self, te: QtWidgets.QTextEdit, who: str, msg: str):
        te.append(f"<p><b>{who}:</b> {html.escape(msg)}</p>")
        te.verticalScrollBar().setValue(te.verticalScrollBar().maximum())

    def _set_wait(self, btn: QtWidgets.QPushButton, waiting: bool):
        if waiting:
            btn.setEnabled(False)
            btn.setText("Pensando...")
        else:
            btn.setEnabled(True)
            original = getattr(btn, "_original_text", "Enviar")
            btn.setText(original)

    # ----- cromo / menú -----
    def mousePressEvent(self, e):
        self._clickPos = e.globalPos()

    def _mover_ventana(self, e):
        if not self.isMaximized() and e.buttons() == QtCore.Qt.LeftButton:
            self.move(self.pos() + e.globalPos() - self._clickPos)
            self._clickPos = e.globalPos()
            e.accept()

    def _mover_menu(self):
        width = self.frame_lateral.width()
        target = 200 if width == 0 else 0
        self.boton_menu.setText("Menú" if target == 200 else "")
        anim = QPropertyAnimation(self.frame_lateral, b"minimumWidth")
        anim.setDuration(300)
        anim.setStartValue(width)
        anim.setEndValue(target)
        anim.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
        anim.start()
        self._anim = anim
