"""Transactions list view — search, filter, add, edit, delete."""
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QAbstractItemView, QFrame, QSizePolicy, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QKeySequence, QShortcut

import database as db
from styles import BG, SURFACE, CARD, BORDER, BLUE, GREEN, RED, TEXT, SUBTEXT, MUTED
from .add_dialog import AddTransactionDialog

COLS = ["Date", "Description", "Tags", "Type", "Amount"]


class TransactionsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[dict] = []
        self._build_ui()
        # Ctrl+N shortcut
        shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut.activated.connect(self._add)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        # ── Header ────────────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("Transactions")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()

        self.btn_add = QPushButton("＋  Add Transaction")
        self.btn_add.setObjectName("primary")
        self.btn_add.setFixedHeight(36)
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.setToolTip("Ctrl+N")
        header.addWidget(self.btn_add)
        root.addLayout(header)

        # ── Filters ────────────────────────────────────────────────────────
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Search description, tags, notes…")
        self.search_box.setFixedHeight(36)
        self.search_box.setClearButtonEnabled(True)
        filter_row.addWidget(self.search_box, 3)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["All Types", "Income", "Expense"])
        self.type_combo.setFixedHeight(36)
        self.type_combo.setMinimumWidth(130)
        filter_row.addWidget(self.type_combo, 1)

        self.tag_combo = QComboBox()
        self.tag_combo.addItem("All Tags")
        self.tag_combo.setFixedHeight(36)
        self.tag_combo.setMinimumWidth(140)
        filter_row.addWidget(self.tag_combo, 1)

        root.addLayout(filter_row)

        # ── Table ─────────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(len(COLS))
        self.table.setHorizontalHeaderLabels(COLS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.setSortingEnabled(True)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.table.setRowHeight(0, 44)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)        # Date
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)      # Description
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)      # Tags
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)        # Type
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)        # Amount
        self.table.setColumnWidth(0, 110)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 130)

        root.addWidget(self.table, 1)

        # ── Action buttons ────────────────────────────────────────────────
        action_row = QHBoxLayout()

        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(f"color: {SUBTEXT}; font-size: 12px;")
        action_row.addWidget(self._count_lbl)
        action_row.addStretch()

        self.btn_edit = QPushButton("✏  Edit")
        self.btn_edit.setFixedHeight(34)
        self.btn_edit.setEnabled(False)
        self.btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_delete = QPushButton("🗑  Delete")
        self.btn_delete.setObjectName("danger")
        self.btn_delete.setFixedHeight(34)
        self.btn_delete.setEnabled(False)
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)

        action_row.addWidget(self.btn_edit)
        action_row.addWidget(self.btn_delete)
        root.addLayout(action_row)

        # ── Signals ────────────────────────────────────────────────────────
        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.table.itemSelectionChanged.connect(self._on_selection)
        self.table.doubleClicked.connect(self._edit)

        # Debounce search
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self._load)
        self.search_box.textChanged.connect(self._search_timer.start)
        self.type_combo.currentIndexChanged.connect(self._load)
        self.tag_combo.currentIndexChanged.connect(self._load)

        self.refresh()

    # ── Data ───────────────────────────────────────────────────────────────────

    def refresh(self):
        # Refresh tag combo
        current_tag = self.tag_combo.currentText()
        self.tag_combo.blockSignals(True)
        self.tag_combo.clear()
        self.tag_combo.addItem("All Tags")
        for tag in db.get_all_tags():
            self.tag_combo.addItem(tag)
        idx = self.tag_combo.findText(current_tag)
        self.tag_combo.setCurrentIndex(max(0, idx))
        self.tag_combo.blockSignals(False)

        self._load()

    def _load(self):
        search      = self.search_box.text().strip()
        type_text   = self.type_combo.currentText()
        tag_text    = self.tag_combo.currentText()

        type_filter = "" if type_text == "All Types" else type_text.lower()
        tag_filter  = "" if tag_text  == "All Tags"  else tag_text

        self._rows = db.get_transactions(search, type_filter, tag_filter)
        self._populate_table()

    def _populate_table(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self._rows))

        for r_idx, t in enumerate(self._rows):
            self.table.setRowHeight(r_idx, 44)

            # Date
            try:
                d = datetime.strptime(t["date"], "%Y-%m-%d")
                date_str = d.strftime("%d/%m/%Y")
            except Exception:
                date_str = t["date"]
            self._cell(r_idx, 0, date_str, align=Qt.AlignmentFlag.AlignCenter)

            # Description
            self._cell(r_idx, 1, t["description"])

            # Tags
            self._cell(r_idx, 2, t["tags"], color=SUBTEXT)

            # Type badge
            is_income = t["type"] == "income"
            type_item = QTableWidgetItem("↑ Income" if is_income else "↓ Expense")
            type_item.setForeground(QColor(GREEN if is_income else RED))
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(r_idx, 3, type_item)

            # Amount
            sign  = "+" if is_income else "−"
            color = GREEN if is_income else RED
            amt_item = QTableWidgetItem(f"{sign} €{t['amount']:,.2f}")
            amt_item.setForeground(QColor(color))
            amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            amt_item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            self.table.setItem(r_idx, 4, amt_item)

        self.table.setSortingEnabled(True)
        total = len(self._rows)
        self._count_lbl.setText(f"{total} transaction{'s' if total != 1 else ''}")
        self._on_selection()

    def _cell(self, row: int, col: int, text: str, align=None, color: str = TEXT):
        item = QTableWidgetItem(text)
        item.setForeground(QColor(color))
        if align:
            item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
        else:
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, col, item)

    def _selected_transaction(self) -> dict | None:
        rows = self.table.selectedItems()
        if not rows:
            return None
        row_idx = self.table.currentRow()
        if row_idx < 0 or row_idx >= len(self._rows):
            return None
        return self._rows[row_idx]

    def _on_selection(self):
        selected = bool(self.table.selectedItems())
        self.btn_edit.setEnabled(selected)
        self.btn_delete.setEnabled(selected)

    # ── Actions ────────────────────────────────────────────────────────────────

    def _add(self):
        dlg = AddTransactionDialog(self)
        if dlg.exec():
            self._notify_parent()

    def _edit(self):
        t = self._selected_transaction()
        if not t:
            return
        dlg = AddTransactionDialog(self, transaction=t)
        if dlg.exec():
            self._notify_parent()

    def _delete(self):
        t = self._selected_transaction()
        if not t:
            return
        msg = QMessageBox(self)
        msg.setWindowTitle("Delete Transaction")
        msg.setText(f"Delete <b>{t['description']}</b>?")
        msg.setInformativeText("This cannot be undone.")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
        msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
        msg.setStyleSheet(f"QMessageBox {{ background-color: {CARD}; }}")
        if msg.exec() == QMessageBox.StandardButton.Yes:
            db.delete_transaction(t["id"])
            self._notify_parent()

    def _notify_parent(self):
        """Tell the main window to refresh all views."""
        main = self.window()
        if hasattr(main, "refresh_all"):
            main.refresh_all()
