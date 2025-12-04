from PyQt5 import QtWidgets
import sys
from load.load_ventana_menu import Load_ventana_menu

def main():
    app=QtWidgets.QApplication(sys.argv)
    ventana = Load_ventana_menu()
    ventana.show()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()