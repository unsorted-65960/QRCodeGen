# controllers/connection_manager_controller.py
import traceback
from PySide6.QtWidgets import QMessageBox
from sqlalchemy import inspect
from database.connection_manager import get_engine, test_connection, build_connection_url
from utils.config_manager import load_config, save_config
from views.connection_manager_view import ConnectionManagerView


class ConnectionManagerController:
    def __init__(self, on_saved=None):
        """Initialize the connection manager window."""
        self.view = ConnectionManagerView()
        self.engine = None
        self.on_saved = on_saved

        # Load existing config (if present)
        self.current_config = load_config() or {}
        if self.current_config:
            self.view.populate_form(self.current_config)
            self.view.show_status_message("Loaded existing configuration.")

        # Connect view signals
        self._connect_signals()

    # ----------------------------------------------------------------------
    def _connect_signals(self):
        v = self.view
        v.test_clicked.connect(self.handle_test_connection)
        v.fetch_tables_clicked.connect(self.handle_fetch_tables)
        v.fetch_columns_clicked.connect(self.handle_fetch_columns)
        v.save_clicked.connect(self.handle_save_config)
        v.save_columns_clicked.connect(self.handle_save_columns)

    # ----------------------------------------------------------------------
    def show(self):
        """Display the view."""
        self.view.show()

    # ----------------------------------------------------------------------
    def handle_test_connection(self, config: dict):
        """Try to establish a connection using provided credentials."""
        self.view.show_status_message("Testing database connection...")
        try:
            success, message = test_connection(config)
            if success:
                self.engine = get_engine()  # refresh engine
                self.view.show_test_result(True, message)
            else:
                self.view.show_test_result(False, message)
        except Exception as e:
            self.view.show_test_result(False, str(e))
            traceback.print_exc()

    # ----------------------------------------------------------------------
    def handle_fetch_tables(self, config: dict):
        """Fetch available table names from the connected database."""
        try:
            self.engine = self._create_engine_from_config(config)
            insp = inspect(self.engine)
            tables = insp.get_table_names()
            self.view.set_tables(tables)
        except Exception as e:
            msg = f"Failed to fetch tables: {e}"
            self.view.show_status_message(msg, error=True)
            traceback.print_exc()

    # ----------------------------------------------------------------------
    def handle_fetch_columns(self, config: dict, table_name: str):
        """Fetch column names for the selected table."""
        try:
            self.engine = self._create_engine_from_config(config)
            insp = inspect(self.engine)
            cols = [c["name"] for c in insp.get_columns(table_name)]
            self.view.set_columns(cols, preselected=config.get("columns"))
        except Exception as e:
            msg = f"Failed to fetch columns for '{table_name}': {e}"
            self.view.show_status_message(msg, error=True)
            traceback.print_exc()

    # ----------------------------------------------------------------------
    def handle_save_config(self, config: dict):
        """Save the current config (without necessarily saving selected columns)."""
        try:
            save_config(config)
            self.view.show_status_message("Configuration saved successfully.")
            QMessageBox.information(self.view, "Saved", "Connection settings saved successfully!")
            if callable(self.on_saved):
                self.on_saved()
        except Exception as e:
            msg = f"Error saving configuration: {e}"
            self.view.show_status_message(msg, error=True)
            traceback.print_exc()

    # ----------------------------------------------------------------------
    def handle_save_columns(self, selected_columns: list):
        """Save the selected columns back into the configuration JSON."""
        try:
            cfg = self.view.collect_config()
            cfg["columns"] = selected_columns
            save_config(cfg)
            self.view.show_status_message(f"Saved {len(selected_columns)} column(s) to configuration.")
            QMessageBox.information(self.view, "Columns Saved",
                                    f"{len(selected_columns)} columns have been saved to connection.json")
            if callable(self.on_saved):
                self.on_saved()
        except Exception as e:
            msg = f"Error saving columns: {e}"
            self.view.show_status_message(msg, error=True)
            traceback.print_exc()

    # ----------------------------------------------------------------------
    def _create_engine_from_config(self, config: dict):
        """Build a temporary engine from config (used for table/column fetching)."""
        from sqlalchemy import create_engine
        url = build_connection_url(config)
        engine = create_engine(url, echo=False, future=True)
        return engine
