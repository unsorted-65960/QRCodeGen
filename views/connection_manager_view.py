# views/connection_manager_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QListWidget,
    QListWidgetItem, QTextEdit, QMessageBox, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal


class ConnectionManagerView(QWidget):
    # Signals to be connected by controller
    test_clicked = Signal(dict)
    save_clicked = Signal(dict)
    fetch_tables_clicked = Signal(dict)
    fetch_columns_clicked = Signal(dict, str)  # config, table_name
    save_columns_clicked = Signal(list)  # list of selected columns

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database Connection Manager")
        self.resize(820, 620)
        self._build_ui()
        self._connect_signals()

    # ---------------- UI construction ----------------
    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Top form: connection settings ---
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.db_type = QComboBox()
        self.db_type.addItems(["mssql", "mysql", "sqlite"])
        self.host = QLineEdit()
        self.port = QLineEdit()
        self.db_name = QLineEdit()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.driver = QLineEdit()
        self.driver.setPlaceholderText("e.g. ODBC Driver 17 for SQL Server (optional)")

        form_layout.addRow("DB Type:", self.db_type)
        form_layout.addRow("Host / Server:", self.host)
        form_layout.addRow("Port:", self.port)
        form_layout.addRow("Database Name:", self.db_name)
        form_layout.addRow("Username:", self.username)
        form_layout.addRow("Password:", self.password)
        form_layout.addRow("Driver:", self.driver)

        main_layout.addLayout(form_layout)

        # --- Buttons row ---
        btn_row = QHBoxLayout()
        self.test_btn = QPushButton("🔎 Test Connection")
        self.fetch_tables_btn = QPushButton("📋 Fetch Tables")
        self.fetch_columns_btn = QPushButton("🔽 Fetch Columns")
        self.save_config_btn = QPushButton("💾 Save Configuration")
        self.save_columns_btn = QPushButton("✅ Save Selected Columns")
        self.close_btn = QPushButton("Close")

        # Reasonable default states
        self.fetch_tables_btn.setEnabled(False)
        self.fetch_columns_btn.setEnabled(False)
        self.save_columns_btn.setEnabled(False)

        btn_row.addWidget(self.test_btn)
        btn_row.addSpacing(6)
        btn_row.addWidget(self.fetch_tables_btn)
        btn_row.addWidget(self.fetch_columns_btn)
        btn_row.addWidget(self.save_columns_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.save_config_btn)
        btn_row.addWidget(self.close_btn)

        main_layout.addLayout(btn_row)

        # --- Middle: table selector + columns list ---
        mid_row = QHBoxLayout()

        left_col = QVBoxLayout()
        left_col.addWidget(QLabel("Target Table:"))
        self.table_selector = QComboBox()
        left_col.addWidget(self.table_selector)

        # Spacer to keep UI balanced
        left_col.addItem(QSpacerItem(12, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        mid_row.addLayout(left_col, 1)

        right_col = QVBoxLayout()
        right_col.addWidget(QLabel("Available Columns: (click to include)"))
        self.columns_list = QListWidget()
        self.columns_list.setAlternatingRowColors(True)
        self.columns_list.itemClicked.connect(self._toggle_item_check)  # ✅ toggle on click
        self.columns_list.setToolTip("Click on column names to check or uncheck.")
        self.columns_list.setStyleSheet("""
            QListWidget::item {
                padding: 4px;
            }
            QListWidget::item:checked {
                background-color: #d0ebff;
            }
        """)
        right_col.addWidget(self.columns_list, 3)

        # Hint label
        hint = QLabel("💡 Tip: Click on column names to select or deselect.")
        hint.setStyleSheet("color: gray; font-size: 9pt;")
        right_col.addWidget(hint)

        mid_row.addLayout(right_col, 3)
        main_layout.addLayout(mid_row)

        # --- Bottom: status/log area ---
        main_layout.addWidget(QLabel("Status / Logs:"))
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setFixedHeight(140)
        main_layout.addWidget(self.status_log)

    # ---------------- Signal wiring ----------------
    def _connect_signals(self):
        self.test_btn.clicked.connect(self._on_test_clicked)
        self.fetch_tables_btn.clicked.connect(self._on_fetch_tables_clicked)
        self.fetch_columns_btn.clicked.connect(self._on_fetch_columns_clicked)
        self.save_config_btn.clicked.connect(self._on_save_config_clicked)
        self.save_columns_btn.clicked.connect(self._on_save_columns_clicked)
        self.close_btn.clicked.connect(self.close)

        # Toggle sensible defaults when db_type changes
        self.db_type.currentTextChanged.connect(self._on_db_type_changed)
        self._on_db_type_changed(self.db_type.currentText())

    # ----------------- UI helpers -------------------
    def _on_db_type_changed(self, db_type: str):
        db_type = db_type.lower()
        if db_type == "sqlite":
            # SQLite only needs a file path in "Database Name"
            self.host.setEnabled(False)
            self.port.setEnabled(False)
            self.username.setEnabled(False)
            self.password.setEnabled(False)
            self.driver.setEnabled(False)
            self.host.setPlaceholderText("Not used for SQLite")
            self.port.setPlaceholderText("Not used for SQLite")
        else:
            self.host.setEnabled(True)
            self.port.setEnabled(True)
            self.username.setEnabled(True)
            self.password.setEnabled(True)
            self.driver.setEnabled(True)
            # set defaults for common DBs
            if db_type == "mssql" and not self.port.text():
                self.port.setText("1433")
            if db_type == "mysql" and not self.port.text():
                self.port.setText("3306")

    def _add_status(self, message: str, error: bool = False):
        prefix = "❌ " if error else "✅ "
        self.status_log.append(prefix + message)

    # ----------------- Button callbacks (emit signals) -------------------
    def _on_test_clicked(self):
        cfg = self.collect_config()
        self._add_status("Testing database connection...")
        self.test_clicked.emit(cfg)

    def _on_fetch_tables_clicked(self):
        cfg = self.collect_config()
        self._add_status("Fetching tables...")
        self.fetch_tables_clicked.emit(cfg)

    def _on_fetch_columns_clicked(self):
        cfg = self.collect_config()
        table = self.table_selector.currentText()
        if not table:
            QMessageBox.warning(self, "No Table Selected", "Please select a table first.")
            return
        self._add_status(f"Fetching columns for table: {table}")
        self.fetch_columns_clicked.emit(cfg, table)

    def _on_save_config_clicked(self):
        cfg = self.collect_config()
        self._add_status("Saving configuration...")
        self.save_clicked.emit(cfg)

    def _on_save_columns_clicked(self):
        selected = self.get_selected_columns()
        if not selected:
            QMessageBox.information(self, "No Columns Selected", "Please select at least one column to save.")
            return
        self._add_status(f"Saving {len(selected)} selected column(s).")
        self.save_columns_clicked.emit(selected)

    # ----------------- Public helpers for controller -------------------
    def collect_config(self) -> dict:
        """Return the form values as a config dict."""
        cfg = {
            "db_type": self.db_type.currentText(),
            "host": self.host.text().strip(),
            "port": self.port.text().strip(),
            "database": self.db_name.text().strip(),
            "username": self.username.text().strip(),
            "password": self.password.text(),
            "driver": self.driver.text().strip(),
            "table": self.table_selector.currentText(),
            "columns": self.get_selected_columns()
        }
        return cfg

    def populate_form(self, config: dict):
        """Populate the form with an existing config dict (if any)."""
        if not config:
            return
        self.db_type.setCurrentText(config.get("db_type", self.db_type.currentText()))
        self.host.setText(config.get("host", ""))
        self.port.setText(str(config.get("port", "")))
        self.db_name.setText(config.get("database", ""))
        self.username.setText(config.get("username", ""))
        self.password.setText(config.get("password", ""))
        self.driver.setText(config.get("driver", ""))

        cols = config.get("columns", [])
        if cols:
            if config.get("table"):
                self.table_selector.setCurrentText(config["table"])
            for i in range(self.columns_list.count()):
                item = self.columns_list.item(i)
                if item.text() in cols:
                    item.setCheckState(Qt.Checked)
        self.fetch_tables_btn.setEnabled(True)

    def set_tables(self, tables: list):
        """Populate the table selector with a list of table names."""
        self.table_selector.clear()
        for t in tables:
            self.table_selector.addItem(str(t))
        if tables:
            self.fetch_columns_btn.setEnabled(True)
            self._add_status(f"Found {len(tables)} table(s).")
        else:
            self.fetch_columns_btn.setEnabled(False)
            self._add_status("No tables found.", error=True)

    def set_columns(self, columns: list, preselected: list | None = None):
        """Populate the columns list with checkable items."""
        self.columns_list.clear()
        for col in columns:
            item = QListWidgetItem(str(col))
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.columns_list.addItem(item)

        if preselected:
            for i in range(self.columns_list.count()):
                item = self.columns_list.item(i)
                if item.text() in preselected:
                    item.setCheckState(Qt.Checked)
        self.save_columns_btn.setEnabled(True)
        self._add_status(f"Loaded {len(columns)} column(s).")

    def get_selected_columns(self) -> list:
        """Return the list of columns the admin has checked."""
        cols = []
        for i in range(self.columns_list.count()):
            item = self.columns_list.item(i)
            if item.checkState() == Qt.Checked:
                cols.append(item.text())
        return cols

    def _toggle_item_check(self, item):
        """Toggle checkbox when clicking anywhere on a column row."""
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)

    def show_test_result(self, success: bool, message: str):
        """Controller can call this to display connection test results."""
        if success:
            self._add_status(message)
            self.fetch_tables_btn.setEnabled(True)
        else:
            self._add_status(message, error=True)
            self.fetch_tables_btn.setEnabled(False)
            self.fetch_columns_btn.setEnabled(False)
            self.save_columns_btn.setEnabled(False)

    def show_status_message(self, message: str, error: bool = False):
        """Generic status display method."""
        self._add_status(message, error)

    # ---------------- Utility: clear UI ----------------
    def clear_all(self):
        self.host.clear()
        self.port.clear()
        self.db_name.clear()
        self.username.clear()
        self.password.clear()
        self.driver.clear()
        self.table_selector.clear()
        self.columns_list.clear()
        self.status_log.clear()
        self.fetch_tables_btn.setEnabled(False)
        self.fetch_columns_btn.setEnabled(False)
        self.save_columns_btn.setEnabled(False)
