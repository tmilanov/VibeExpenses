"""Main application window with sidebar navigation."""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QButtonGroup, QFrame,
)
from PyQt6.QtCore import Qt

import database as db
from styles import STYLE, BG, SURFACE, CARD, BORDER, BLUE, TEXT, SUBTEXT
from .dashboard import DashboardView
from .transactions import TransactionsView
from .charts import ChartsView


class Sidebar(QWidget):
    """Left navigation panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(210)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {SURFACE};
                border-right: 1px solid {BORDER};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 24, 12, 20)
        layout.setSpacing(4)

        # Brand
        brand_row = QHBoxLayout()
        brand_row.setSpacing(8)
        icon_lbl = QLabel("💰")
        icon_lbl.setStyleSheet("font-size: 20px; border: none; background: transparent;")
        name_lbl = QLabel("Vibe Expenses")
        name_lbl.setObjectName("appTitle")
        name_lbl.setStyleSheet(
            f"color: {TEXT}; font-size: 15px; font-weight: 700; border: none; background: transparent;"
        )
        brand_row.addWidget(icon_lbl)
        brand_row.addWidget(name_lbl)
        brand_row.addStretch()
        layout.addLayout(brand_row)

        # Divider
        layout.addSpacing(16)
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER}; border: none; background: {BORDER}; max-height: 1px;")
        layout.addWidget(sep)
        layout.addSpacing(12)

        # Nav buttons
        self.btn_dashboard    = self._make_nav("📊   Dashboard",    "Overview of your finances")
        self.btn_transactions = self._make_nav("💳   Transactions", "View & manage all entries")
        self.btn_charts       = self._make_nav("📈   Charts",       "Visualise your data")

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        for i, btn in enumerate([self.btn_dashboard, self.btn_transactions, self.btn_charts]):
            self._group.addButton(btn, i)
            layout.addWidget(btn)

        layout.addStretch()

        # Footer
        footer = QLabel("v1.0  ·  SQLite")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(
            f"color: {SUBTEXT}; font-size: 10px; border: none; background: transparent;"
        )
        layout.addWidget(footer)

        self.btn_dashboard.setChecked(True)

    @staticmethod
    def _make_nav(text: str, tooltip: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("nav")
        btn.setCheckable(True)
        btn.setAutoExclusive(False)   # managed by QButtonGroup
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.setFixedHeight(42)
        return btn


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        db.init_db()

        self.setWindowTitle("Vibe Expenses")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self.setStyleSheet(STYLE)

        # ── Root layout ────────────────────────────────────────────────────
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ────────────────────────────────────────────────────────
        self.sidebar = Sidebar()
        root.addWidget(self.sidebar)

        # ── Page stack ────────────────────────────────────────────────────
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.pg_dashboard    = DashboardView(self)
        self.pg_transactions = TransactionsView(self)
        self.pg_charts       = ChartsView(self)

        self.stack.addWidget(self.pg_dashboard)
        self.stack.addWidget(self.pg_transactions)
        self.stack.addWidget(self.pg_charts)

        # ── Navigation signals ─────────────────────────────────────────────
        self.sidebar.btn_dashboard.clicked.connect(lambda: self._navigate(0))
        self.sidebar.btn_transactions.clicked.connect(lambda: self._navigate(1))
        self.sidebar.btn_charts.clicked.connect(lambda: self._navigate(2))

        # Show dashboard on start
        self.pg_dashboard.refresh()

    # ── Slots ──────────────────────────────────────────────────────────────────

    def _navigate(self, index: int):
        self.stack.setCurrentIndex(index)
        page = self.stack.currentWidget()
        if hasattr(page, "refresh"):
            page.refresh()

    def refresh_all(self):
        """Refresh every page after a data change."""
        self.pg_dashboard.refresh()
        self.pg_transactions.refresh()
        # Charts: only refresh the visible one to avoid heavy redraws
        self.pg_charts.refresh()
