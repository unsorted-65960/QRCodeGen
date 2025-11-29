from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QSpinBox,
    QAbstractItemView, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer
from functools import partial


class MainView(QWidget):
    refresh_requested = Signal()
    print_requested = Signal(object, object)
    connect_db_clicked = Signal()
    generate_qr_clicked = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Product Label Manager")
        self.resize(1250, 650)
        self._products = []
        self._checked_state = {}  # Persist checkbox + qty between refreshes

        main_layout = QVBoxLayout()
        top_bar = QHBoxLayout()

        # --- Top Buttons ---
        self.connect_btn = QPushButton("🔌 Connect DB")
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.print_btn = QPushButton("🖨️ Print Labels")

        top_bar.addWidget(self.connect_btn)
        top_bar.addStretch()
        top_bar.addWidget(self.refresh_btn)
        top_bar.addWidget(self.print_btn)
        main_layout.addLayout(top_bar)

        # --- Table setup ---
        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #fafafa;
                alternate-background-color: #f5f5f5;
                gridline-color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #f2f2f2;
                font-weight: bold;
                border: none;
                padding: 6px;
            }
        """)

        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        # --- Button Connections ---
        self.connect_btn.clicked.connect(self.connect_db_clicked.emit)
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        self.print_btn.clicked.connect(self.emit_print)

    # ----------------------------------------------------------------------
    def populate_table(self, products: list[dict]):
        """Populate table while preserving scroll, focus, and checkbox/quantity states."""
        table = self.table
        scroll_bar = table.verticalScrollBar()
        saved_scroll = scroll_bar.value()
        saved_focus = QApplication.focusWidget()

        # Capture current selection state before clearing
        self._capture_state()

        table.setUpdatesEnabled(False)
        self._products = products
        table.clear()
        table.setRowCount(0)
        table.setColumnCount(0)

        if not products:
            table.setColumnCount(1)
            table.setHorizontalHeaderLabels(["No data found"])
            table.setUpdatesEnabled(True)
            return

        data_columns = [k for k in products[0].keys() if k not in ("qr_status", "qr_hash")]
        headers = ["S.No", "Select", *[h.replace("_", " ").title() for h in data_columns],
                   "QR Status", "Qty", "_qr_hash"]

        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setColumnHidden(len(headers) - 1, True)
        table.setRowCount(len(products))

        for row, product in enumerate(products):
            row_key = str(product.get("qr_hash", row))  # use hash if available
            state = self._checked_state.get(row_key, {"checked": False, "qty": 1})

            # --- S.No
            sno_item = QTableWidgetItem(str(row + 1))
            sno_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 0, sno_item)

            # --- Checkbox
            checkbox = QCheckBox()
            checkbox.setFocusPolicy(Qt.NoFocus)
            checkbox.stateChanged.connect(partial(self.on_checkbox_changed, row))
            table.setCellWidget(row, 1, checkbox)

            # --- Data columns
            for col_idx, key in enumerate(data_columns, start=2):
                item = QTableWidgetItem(str(product.get(key, "")))
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, col_idx, item)

            # --- QR Status
            status_col = len(headers) - 3
            status = product.get("qr_status", "No QR")
            if status == "Has QR":
                item = QTableWidgetItem("✅ Has QR")
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, status_col, item)
            else:
                btn = QPushButton("⚙️ Generate QR")
                btn.setFocusPolicy(Qt.NoFocus)
                btn.clicked.connect(partial(self._on_generate_qr_clicked, product))
                table.setCellWidget(row, status_col, btn)

            # --- Qty SpinBox
            qty_col = len(headers) - 2
            qty_spin = QSpinBox()
            qty_spin.setRange(1, 500)
            qty_spin.setValue(state["qty"])
            qty_spin.setFocusPolicy(Qt.NoFocus)
            qty_spin.setEnabled(state["checked"] and status == "Has QR")
            table.setCellWidget(row, qty_col, qty_spin)

            # --- Hidden hash
            hash_item = QTableWidgetItem(str(product.get("qr_hash", "")))
            table.setItem(row, len(headers) - 1, hash_item)

            # Restore checkbox state
            checkbox.setChecked(state["checked"])

        # Resize columns
        header = table.horizontalHeader()
        for i in range(table.columnCount()):
            mode = QHeaderView.ResizeToContents if i < 2 else QHeaderView.Stretch
            header.setSectionResizeMode(i, mode)

        table.resizeRowsToContents()
        table.setUpdatesEnabled(True)

        # Restore scroll & focus
        def restore_scroll():
            scroll_bar.setValue(min(saved_scroll, scroll_bar.maximum()))
            if saved_focus:
                saved_focus.setFocus()
            QApplication.processEvents()

        QTimer.singleShot(0, restore_scroll)

    # ----------------------------------------------------------------------
    def _capture_state(self):
        """Store checkbox + qty states before refresh."""
        if not self.table.rowCount():
            return

        for row in range(self.table.rowCount()):
            hash_item = self.table.item(row, self.table.columnCount() - 1)
            row_key = hash_item.text() if hash_item else str(row)
            checkbox = self.table.cellWidget(row, 1)
            spinbox = self.table.cellWidget(row, self.table.columnCount() - 2)
            checked = checkbox.isChecked() if checkbox else False
            qty = spinbox.value() if spinbox else 1
            self._checked_state[row_key] = {"checked": checked, "qty": qty}

    # ----------------------------------------------------------------------
    def _on_generate_qr_clicked(self, product):
        """Emit signal to open QR preview window (controller handles refresh)."""
        self.generate_qr_clicked.emit(product)

    # ----------------------------------------------------------------------
    def on_checkbox_changed(self, row, state):
        """Enable or disable quantity spinbox when checkbox toggled."""
        qty_col = self.table.columnCount() - 2
        status_col = self.table.columnCount() - 3
        spinbox = self.table.cellWidget(row, qty_col)
        checkbox = self.table.cellWidget(row, 1)

        if not spinbox:
            return

        status_item = self.table.item(row, status_col)
        has_qr = status_item and "Has QR" in status_item.text()

        if state == 2:  # Checked
            if has_qr:
                spinbox.setEnabled(True)
            else:
                if checkbox:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(False)
                    checkbox.blockSignals(False)
                spinbox.setEnabled(False)
                QMessageBox.information(
                    self,
                    "QR Not Generated",
                    "Please generate a QR for this product before selecting it for printing.",
                )
        elif state == 0:  # Unchecked
            spinbox.setEnabled(False)

        QApplication.processEvents()
        spinbox.repaint()

    # ----------------------------------------------------------------------
    def emit_print(self):
        """Collect selected rows for label printing with correct quantity mapping."""
        selected_products = []
        quantity_map = {}

        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 1)
            if checkbox and checkbox.isChecked():
                row_data = {"_row": row + 1}  # 🧩 store actual table row number

                # Collect visible columns
                for col in range(2, self.table.columnCount() - 3):
                    header = self.table.horizontalHeaderItem(col).text().replace(" ", "_").lower()
                    cell_item = self.table.item(row, col)
                    row_data[header] = cell_item.text() if cell_item else ""

                # Include QR hash (used for image lookup)
                hash_item = self.table.item(row, self.table.columnCount() - 1)
                row_data["qr_hash"] = hash_item.text() if hash_item else ""

                # Quantity from spinbox
                spinbox = self.table.cellWidget(row, self.table.columnCount() - 2)
                qty = spinbox.value() if spinbox else 1

                selected_products.append(row_data)
                quantity_map[row + 1] = qty  # use real row index

        if not selected_products:
            QMessageBox.warning(
                self,
                "No Products Selected",
                "Please select at least one product to print labels."
            )
            return

        # Emit products and correct quantity map
        self.print_requested.emit(selected_products, quantity_map)
