"""Dashboard view — summary cards + recent transactions."""
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QSizePolicy, QPushButton,
    QGridLayout,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import database as db
from styles import (
    BG, SURFACE, CARD, BORDER, BLUE, GREEN, RED,
    YELLOW, TEXT, SUBTEXT, MUTED,
)


# ── Reusable card widget ───────────────────────────────────────────────────────

class SummaryCard(QFrame):
    def __init__(self, title: str, value: str = "—", value_color: str = TEXT,
                 subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("summaryCard")
        self.setStyleSheet(f"""
            QFrame#summaryCard {{
                background-color: {CARD};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 4px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)

        self._title_lbl = QLabel(title.upper())
        self._title_lbl.setObjectName("cardTitle")

        self._value_lbl = QLabel(value)
        self._value_lbl.setObjectName("cardValue")
        self._value_lbl.setStyleSheet(f"color: {value_color}; font-size: 26px; font-weight: 700;")

        self._sub_lbl = QLabel(subtitle)
        self._sub_lbl.setStyleSheet(f"color: {SUBTEXT}; font-size: 11px;")

        layout.addWidget(self._title_lbl)
        layout.addWidget(self._value_lbl)
        if subtitle:
            layout.addWidget(self._sub_lbl)
        layout.addStretch()

    def update_value(self, value: str, color: str = TEXT, subtitle: str = ""):
        self._value_lbl.setText(value)
        self._value_lbl.setStyleSheet(f"color: {color}; font-size: 26px; font-weight: 700;")
        if subtitle:
            self._sub_lbl.setText(subtitle)


# ── Recent transaction row ─────────────────────────────────────────────────────

class RecentRow(QFrame):
    def __init__(self, t: dict, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-bottom: 1px solid {BORDER};
            }}
            QFrame:hover {{ background-color: {SURFACE}; }}
        """)

        row = QHBoxLayout(self)
        row.setContentsMargins(16, 10, 16, 10)
        row.setSpacing(12)

        # Type badge
        is_income = t["type"] == "income"
        badge = QLabel("↑ Income" if is_income else "↓ Expense")
        badge.setObjectName("badge_income" if is_income else "badge_expense")
        badge.setFixedWidth(78)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(badge)

        # Description + tags
        mid = QVBoxLayout()
        mid.setSpacing(2)
        desc_lbl = QLabel(t["description"])
        desc_lbl.setStyleSheet(f"color: {TEXT}; font-weight: 500; border: none;")
        desc_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        mid.addWidget(desc_lbl)
        if t["tags"]:
            tags_lbl = QLabel(t["tags"])
            tags_lbl.setStyleSheet(f"color: {SUBTEXT}; font-size: 11px; border: none;")
            mid.addWidget(tags_lbl)
        row.addLayout(mid)
        row.addStretch()

        # Date
        try:
            d = datetime.strptime(t["date"], "%Y-%m-%d")
            date_str = d.strftime("%d/%m/%Y")
        except Exception:
            date_str = t["date"]
        date_lbl = QLabel(date_str)
        date_lbl.setStyleSheet(f"color: {SUBTEXT}; font-size: 12px; border: none;")
        row.addWidget(date_lbl)

        # Amount
        sign  = "+" if is_income else "−"
        color = GREEN if is_income else RED
        amt_lbl = QLabel(f"{sign} €{t['amount']:,.2f}")
        amt_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        amt_lbl.setStyleSheet(f"color: {color}; font-weight: 700; font-size: 14px; border: none;")
        amt_lbl.setMinimumWidth(110)
        row.addWidget(amt_lbl)


# ── Dashboard view ─────────────────────────────────────────────────────────────

class DashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(24)

        # ── Header ────────────────────────────────────────────────────────
        now = datetime.now()
        header = QHBoxLayout()
        page_title = QLabel("Dashboard")
        page_title.setObjectName("pageTitle")
        month_lbl = QLabel(now.strftime("%B %Y"))
        month_lbl.setStyleSheet(f"color: {SUBTEXT}; font-size: 13px; font-weight: 500;")
        header.addWidget(page_title)
        header.addStretch()
        header.addWidget(month_lbl)
        root.addLayout(header)

        # ── Summary cards ─────────────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        self.card_balance  = SummaryCard("Total Balance",    "€0.00", BLUE,  "all time")
        self.card_income   = SummaryCard("Income",           "€0.00", GREEN, "this month")
        self.card_expenses = SummaryCard("Expenses",         "€0.00", RED,   "this month")
        self.card_net      = SummaryCard("Net Savings",      "€0.00", TEXT,  "this month")

        for card in (self.card_balance, self.card_income, self.card_expenses, self.card_net):
            cards_row.addWidget(card)

        root.addLayout(cards_row)

        # ── Recent transactions ────────────────────────────────────────────
        recent_label = QLabel("Recent Transactions")
        recent_label.setObjectName("sectionTitle")
        root.addWidget(recent_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._recent_container = QWidget()
        self._recent_container.setStyleSheet(f"""
            QWidget {{
                background-color: {CARD};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)
        self._recent_layout = QVBoxLayout(self._recent_container)
        self._recent_layout.setContentsMargins(0, 0, 0, 0)
        self._recent_layout.setSpacing(0)

        self._empty_label = QLabel("No transactions yet.\nAdd your first one from the Transactions tab!")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(f"color: {SUBTEXT}; padding: 40px; border: none;")
        self._recent_layout.addWidget(self._empty_label)

        scroll.setWidget(self._recent_container)
        root.addWidget(scroll, 1)

        self.refresh()

    def refresh(self):
        now = datetime.now()
        summary = db.get_monthly_summary(now.year, now.month)
        balance = db.get_total_balance()
        net     = summary["income"] - summary["expenses"]
        net_color = GREEN if net >= 0 else RED

        self.card_balance.update_value(f"€{balance:,.2f}", BLUE)
        self.card_income.update_value(f"€{summary['income']:,.2f}", GREEN)
        self.card_expenses.update_value(f"€{summary['expenses']:,.2f}", RED)
        self.card_net.update_value(f"€{net:,.2f}", net_color)

        # Rebuild recent transactions
        while self._recent_layout.count():
            item = self._recent_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        recent = db.get_recent_transactions(10)
        if not recent:
            self._empty_label = QLabel(
                "No transactions yet.\nAdd your first one from the Transactions tab!"
            )
            self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._empty_label.setStyleSheet(f"color: {SUBTEXT}; padding: 40px; border: none;")
            self._recent_layout.addWidget(self._empty_label)
        else:
            for t in recent:
                row = RecentRow(t)
                self._recent_layout.addWidget(row)
            self._recent_layout.addStretch()
