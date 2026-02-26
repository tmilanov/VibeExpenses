"""Dialog for adding or editing a transaction."""
from datetime import date as Date

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QDoubleSpinBox,
    QDateEdit, QPushButton, QWidget, QButtonGroup,
    QCompleter, QFrame,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

import database as db
from styles import BG, SURFACE, CARD, BORDER, BLUE, GREEN, RED, TEXT, SUBTEXT


class AddTransactionDialog(QDialog):
    def __init__(self, parent=None, transaction: dict = None):
        super().__init__(parent)
        self._transaction = transaction
        is_edit = transaction is not None

        self.setWindowTitle("Edit Transaction" if is_edit else "Add Transaction")
        self.setModal(True)
        self.setMinimumWidth(460)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(20)

        # ── Title ──────────────────────────────────────────────────────────
        title = QLabel("Edit Transaction" if is_edit else "New Transaction")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        # ── Type toggle ────────────────────────────────────────────────────
        type_row = QHBoxLayout()
        type_label = QLabel("Type")
        type_label.setObjectName("cardTitle")
        type_label.setFixedWidth(90)
        type_row.addWidget(type_label)

        self.btn_income  = QPushButton("↑  Income")
        self.btn_expense = QPushButton("↓  Expense")
        self.btn_income.setObjectName("toggle_income")
        self.btn_expense.setObjectName("toggle_expense")
        self.btn_income.setCheckable(True)
        self.btn_expense.setCheckable(True)
        self.btn_income.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_expense.setCursor(Qt.CursorShape.PointingHandCursor)

        self._type_group = QButtonGroup(self)
        self._type_group.addButton(self.btn_income,  0)
        self._type_group.addButton(self.btn_expense, 1)
        self._type_group.setExclusive(True)

        type_row.addWidget(self.btn_income)
        type_row.addWidget(self.btn_expense)
        type_row.addStretch()
        root.addLayout(type_row)

        # ── Form ───────────────────────────────────────────────────────────
        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        def label(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setObjectName("cardTitle")
            return lbl

        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setFixedHeight(36)
        form.addRow(label("Date"), self.date_edit)

        # Description
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("e.g. Grocery run, Monthly salary…")
        self.desc_edit.setFixedHeight(36)
        form.addRow(label("Description"), self.desc_edit)

        # Amount
        amount_row = QHBoxLayout()
        euro_lbl = QLabel("€")
        euro_lbl.setStyleSheet(f"color: {SUBTEXT}; font-size: 16px; font-weight: 600;")
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 9_999_999.99)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setSingleStep(1.0)
        self.amount_spin.setValue(0.00)
        self.amount_spin.setFixedHeight(36)
        self.amount_spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        amount_row.addWidget(euro_lbl)
        amount_row.addWidget(self.amount_spin)
        form.addRow(label("Amount"), amount_row)

        # Tags
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Food, Transport, Salary  (comma-separated)")
        self.tags_edit.setFixedHeight(36)
        known_tags = db.get_all_tags()
        if known_tags:
            completer = QCompleter(known_tags)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.tags_edit.setCompleter(completer)
        form.addRow(label("Tags"), self.tags_edit)

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Optional note…")
        self.notes_edit.setFixedHeight(72)
        form.addRow(label("Notes"), self.notes_edit)

        root.addLayout(form)

        # ── Divider ────────────────────────────────────────────────────────
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(line)

        # ── Buttons ────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedHeight(36)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Save Transaction" if not is_edit else "Update Transaction")
        self.btn_save.setObjectName("primary")
        self.btn_save.setFixedHeight(36)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.btn_save)

        root.addLayout(btn_row)

        # ── Signals ────────────────────────────────────────────────────────
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._save)

        # ── Populate if editing ────────────────────────────────────────────
        if is_edit:
            self._populate(transaction)
        else:
            self.btn_expense.setChecked(True)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _populate(self, t: dict):
        if t["type"] == "income":
            self.btn_income.setChecked(True)
        else:
            self.btn_expense.setChecked(True)

        parts = t["date"].split("-")          # stored as YYYY-MM-DD
        if len(parts) == 3:
            self.date_edit.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))

        self.desc_edit.setText(t["description"])
        self.amount_spin.setValue(float(t["amount"]))
        self.tags_edit.setText(t["tags"])
        self.notes_edit.setPlainText(t["notes"])

    def _save(self):
        desc = self.desc_edit.text().strip()
        if not desc:
            self.desc_edit.setFocus()
            self.desc_edit.setStyleSheet(f"border: 1px solid #f85149;")
            return
        self.desc_edit.setStyleSheet("")

        amount = self.amount_spin.value()
        if amount <= 0:
            return

        q_date = self.date_edit.date()
        date_str = f"{q_date.year():04d}-{q_date.month():02d}-{q_date.day():02d}"
        type_   = "income" if self.btn_income.isChecked() else "expense"
        tags    = self.tags_edit.text().strip()
        notes   = self.notes_edit.toPlainText().strip()

        if self._transaction:
            db.update_transaction(self._transaction["id"], date_str, desc, amount, type_, tags, notes)
        else:
            db.add_transaction(date_str, desc, amount, type_, tags, notes)

        self.accept()
