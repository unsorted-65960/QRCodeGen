# main.py
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

# ensure data folders exist early
Path("data/output").mkdir(parents=True, exist_ok=True)

from database.database import init_db, Base
from controllers.main_controller import MainController

def main():
    app = QApplication(sys.argv)

    # apply qt-material base theme (you can change the xml name)
    apply_stylesheet(app, theme="light_blue.xml")

    # load custom QSS from assets/style.qss if present
    qss_path = Path(__file__).parent / "assets" / "style.qss"
    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(app.styleSheet() + "\n" + f.read())

    # initialize database (creates tables)
    init_db(Base)

    # launch main controller (table view is main)
    controller = MainController()
    controller.show_main_window()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
