"""Color palette and QSS stylesheet for Vibe Expenses (dark fintech theme)."""

# ── Palette ───────────────────────────────────────────────────────────────────
BG       = "#0d1117"
SURFACE  = "#161b22"
CARD     = "#21262d"
BORDER   = "#30363d"
BLUE     = "#58a6ff"
GREEN    = "#3fb950"
RED      = "#f85149"
YELLOW   = "#d29922"
PURPLE   = "#bc8cff"
TEXT     = "#e6edf3"
SUBTEXT  = "#8b949e"
MUTED    = "#484f58"

# Chart color cycle
CHART_COLORS = [
    "#58a6ff", "#3fb950", "#d29922", "#bc8cff",
    "#ff7b72", "#79c0ff", "#56d364", "#ffa657",
    "#f78166", "#d2a8ff", "#7ee787", "#e3b341",
]

STYLE = f"""
/* ── Global ───────────────────────────────────────────── */
QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: "Segoe UI";
    font-size: 13px;
}}
QMainWindow, QDialog {{
    background-color: {BG};
}}
QToolTip {{
    background-color: {CARD};
    color: {TEXT};
    border: 1px solid {BORDER};
    padding: 4px 8px;
    border-radius: 4px;
}}

/* ── Scrollbars ───────────────────────────────────────── */
QScrollBar:vertical {{
    background: {BG};
    width: 8px;
    border-radius: 4px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {SUBTEXT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {BG};
    height: 8px;
    border-radius: 4px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER};
    border-radius: 4px;
    min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{ background: {SUBTEXT}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Inputs ───────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit, QDoubleSpinBox, QSpinBox, QDateEdit, QComboBox {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 7px 10px;
    selection-background-color: {BLUE};
    selection-color: {BG};
}}
QLineEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus {{
    border: 1px solid {BLUE};
}}
QLineEdit::placeholder, QTextEdit::placeholder {{ color: {MUTED}; }}

QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox QAbstractItemView {{
    background-color: {CARD};
    color: {TEXT};
    border: 1px solid {BORDER};
    selection-background-color: {BLUE};
    selection-color: {BG};
    outline: none;
    padding: 4px;
}}
QComboBox QAbstractItemView::item {{ padding: 6px 10px; border-radius: 4px; }}

QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
QDateEdit::up-button, QDateEdit::down-button {{
    width: 18px;
    border: none;
    background: transparent;
    color: {SUBTEXT};
}}

/* ── Buttons ──────────────────────────────────────────── */
QPushButton {{
    background-color: {CARD};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {SURFACE};
    border-color: {SUBTEXT};
}}
QPushButton:pressed {{ background-color: {BG}; }}
QPushButton:disabled {{
    background-color: {CARD};
    color: {MUTED};
    border-color: {BORDER};
}}

QPushButton#primary {{
    background-color: {BLUE};
    color: {BG};
    border: none;
    font-weight: 600;
}}
QPushButton#primary:hover {{ background-color: #79baff; }}
QPushButton#primary:pressed {{ background-color: #388bfd; }}

QPushButton#success {{
    background-color: {GREEN};
    color: {BG};
    border: none;
    font-weight: 600;
}}
QPushButton#success:hover {{ background-color: #56d364; }}

QPushButton#danger {{
    background-color: transparent;
    color: {RED};
    border: 1px solid {RED};
}}
QPushButton#danger:hover {{ background-color: {RED}; color: {BG}; }}

QPushButton#nav {{
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    color: {SUBTEXT};
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#nav:hover {{ background-color: {CARD}; color: {TEXT}; }}
QPushButton#nav:checked {{
    background-color: {CARD};
    color: {BLUE};
    font-weight: 600;
}}

QPushButton#toggle_income {{
    background-color: transparent;
    color: {SUBTEXT};
    border: 1px solid {BORDER};
    border-radius: 6px 0 0 6px;
    padding: 8px 20px;
    font-weight: 500;
}}
QPushButton#toggle_income:checked {{
    background-color: {GREEN};
    color: {BG};
    border-color: {GREEN};
    font-weight: 600;
}}
QPushButton#toggle_expense {{
    background-color: transparent;
    color: {SUBTEXT};
    border: 1px solid {BORDER};
    border-left: none;
    border-radius: 0 6px 6px 0;
    padding: 8px 20px;
    font-weight: 500;
}}
QPushButton#toggle_expense:checked {{
    background-color: {RED};
    color: {BG};
    border-color: {RED};
    font-weight: 600;
}}

/* ── Table ────────────────────────────────────────────── */
QTableWidget {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: {BG};
    outline: none;
    alternate-background-color: {CARD};
}}
QTableWidget::item {{
    padding: 4px 12px;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: rgba(88, 166, 255, 0.2);
    color: {TEXT};
}}
QTableWidget::item:selected:active {{
    background-color: rgba(88, 166, 255, 0.3);
}}
QHeaderView::section {{
    background-color: {CARD};
    color: {SUBTEXT};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 10px 12px;
    font-weight: 600;
    font-size: 11px;
}}

/* ── Tabs ─────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 0 8px 8px 8px;
    background-color: {SURFACE};
    top: -1px;
}}
QTabBar::tab {{
    background-color: {BG};
    color: {SUBTEXT};
    border: 1px solid {BORDER};
    border-bottom: none;
    padding: 9px 24px;
    margin-right: 2px;
    border-radius: 6px 6px 0 0;
    font-weight: 500;
}}
QTabBar::tab:selected {{
    background-color: {SURFACE};
    color: {BLUE};
    border-bottom: 1px solid {SURFACE};
}}
QTabBar::tab:hover:!selected {{ color: {TEXT}; }}

/* ── Labels ───────────────────────────────────────────── */
QLabel#cardTitle {{
    color: {SUBTEXT};
    font-size: 11px;
    font-weight: 600;
}}
QLabel#cardValue {{
    color: {TEXT};
    font-size: 24px;
    font-weight: 700;
}}
QLabel#cardValueGreen {{
    color: {GREEN};
    font-size: 24px;
    font-weight: 700;
}}
QLabel#cardValueRed {{
    color: {RED};
    font-size: 24px;
    font-weight: 700;
}}
QLabel#sectionTitle {{
    color: {TEXT};
    font-size: 15px;
    font-weight: 600;
}}
QLabel#pageTitle {{
    color: {TEXT};
    font-size: 20px;
    font-weight: 700;
}}
QLabel#appTitle {{
    color: {TEXT};
    font-size: 15px;
    font-weight: 700;
}}
QLabel#badge_income {{
    color: {GREEN};
    background-color: rgba(63, 185, 80, 0.15);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}}
QLabel#badge_expense {{
    color: {RED};
    background-color: rgba(248, 81, 73, 0.15);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}}

/* ── Frame separators ─────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{ color: {BORDER}; }}

/* ── Radio ────────────────────────────────────────────── */
QRadioButton {{ color: {TEXT}; spacing: 8px; }}
QRadioButton::indicator {{
    width: 16px; height: 16px;
    border-radius: 8px;
    border: 2px solid {BORDER};
    background-color: {SURFACE};
}}
QRadioButton::indicator:checked {{
    background-color: {BLUE};
    border-color: {BLUE};
}}
"""
