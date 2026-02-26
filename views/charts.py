"""Charts view — period picker + income/expense bar, spending donut, balance trend."""
import calendar
from datetime import date as Date, datetime, timedelta

import numpy as np
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QFrame, QSizePolicy, QPushButton,
    QDateEdit, QButtonGroup, QStackedWidget,
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal

import database as db
from styles import (
    BG, SURFACE, CARD, BORDER, BLUE, GREEN, RED, YELLOW,
    TEXT, SUBTEXT, MUTED, CHART_COLORS,
)

# ── Matplotlib dark theme ──────────────────────────────────────────────────────
_MPL_RC = {
    "figure.facecolor":   SURFACE,
    "axes.facecolor":     SURFACE,
    "axes.edgecolor":     BORDER,
    "axes.labelcolor":    SUBTEXT,
    "axes.titlecolor":    TEXT,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.spines.left":   False,
    "axes.spines.bottom": True,
    "axes.grid":          True,
    "grid.color":         BORDER,
    "grid.alpha":         0.6,
    "grid.linestyle":     "--",
    "xtick.color":        SUBTEXT,
    "ytick.color":        SUBTEXT,
    "xtick.labelsize":    10,
    "ytick.labelsize":    10,
    "text.color":         TEXT,
    "legend.facecolor":   CARD,
    "legend.edgecolor":   BORDER,
    "legend.labelcolor":  TEXT,
    "legend.fontsize":    10,
}

_PERIOD_BTN_STYLE = f"""
QPushButton#period_btn {{
    background: transparent;
    color: {SUBTEXT};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 500;
}}
QPushButton#period_btn:checked {{
    background-color: {BLUE};
    color: {BG};
    border-color: {BLUE};
    font-weight: 600;
}}
QPushButton#period_btn:hover:!checked {{
    color: {TEXT};
    border-color: {SUBTEXT};
}}
"""


def _setup_ax(fig: Figure, ax):
    for k, v in _MPL_RC.items():
        try:
            plt.rcParams[k] = v
        except Exception:
            pass
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ax.spines["bottom"].set_color(BORDER)
    ax.spines["left"].set_color("none")
    ax.tick_params(colors=SUBTEXT, which="both")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:,.0f}"))


def _no_data(ax, msg: str = "No data for this period."):
    ax.text(0.5, 0.5, msg, transform=ax.transAxes,
            ha="center", va="center", fontsize=13, color=SUBTEXT, style="italic")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


# ── Period helpers ─────────────────────────────────────────────────────────────

def _today() -> Date:
    return Date.today()


def _to_str(d: Date) -> str:
    return d.strftime("%Y-%m-%d")


def _preset_range(name: str) -> tuple[str, str]:
    """Return (date_from, date_to) as 'YYYY-MM-DD' strings, or ('', '') for all time."""
    today = _today()
    if name == "All Time":
        return "", ""
    if name == "This Week":
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        return _to_str(monday), _to_str(sunday)
    if name == "This Month":
        return _to_str(today.replace(day=1)), _to_str(today)
    if name == "Last Month":
        if today.month == 1:
            yr, mo = today.year - 1, 12
        else:
            yr, mo = today.year, today.month - 1
        last_day = calendar.monthrange(yr, mo)[1]
        return _to_str(Date(yr, mo, 1)), _to_str(Date(yr, mo, last_day))
    if name == "This Year":
        return _to_str(today.replace(month=1, day=1)), _to_str(today)
    return "", ""


def _days_in_range(date_from: str, date_to: str) -> int:
    if not date_from or not date_to:
        return 999
    try:
        d0 = datetime.strptime(date_from, "%Y-%m-%d").date()
        d1 = datetime.strptime(date_to,   "%Y-%m-%d").date()
        return (d1 - d0).days + 1
    except Exception:
        return 999


def _label_period(period: str, group_by: str) -> str:
    """Human-readable x-axis label for a period string."""
    try:
        if group_by == "day":
            dt = datetime.strptime(period, "%Y-%m-%d")
            return dt.strftime("%d\n%b")
        else:
            dt = datetime.strptime(period, "%Y-%m")
            return dt.strftime("%b\n'%y")
    except Exception:
        return period


# ── Period picker widget ───────────────────────────────────────────────────────

class PeriodPicker(QWidget):
    """Compact quick-select + custom date range widget."""
    changed = pyqtSignal(str, str)   # (date_from, date_to)

    PRESETS = ["All Time", "This Week", "This Month", "Last Month", "This Year", "Custom"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_PERIOD_BTN_STYLE)
        self._date_from = ""
        self._date_to   = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # ── Preset buttons ─────────────────────────────────────────────────
        presets_row = QHBoxLayout()
        presets_row.setSpacing(6)

        lbl = QLabel("Period:")
        lbl.setStyleSheet(f"color: {SUBTEXT}; font-size: 12px; font-weight: 600;")
        presets_row.addWidget(lbl)

        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)
        self._preset_btns: dict[str, QPushButton] = {}

        for name in self.PRESETS:
            btn = QPushButton(name)
            btn.setObjectName("period_btn")
            btn.setCheckable(True)
            btn.setFixedHeight(28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._btn_group.addButton(btn)
            self._preset_btns[name] = btn
            presets_row.addWidget(btn)

        presets_row.addStretch()
        root.addLayout(presets_row)

        # ── Custom date row (hidden unless Custom selected) ────────────────
        self._custom_row = QWidget()
        self._custom_row.setVisible(False)
        custom_layout = QHBoxLayout(self._custom_row)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.setSpacing(10)

        custom_layout.addWidget(QLabel("From:"))
        self._from_edit = QDateEdit()
        self._from_edit.setDisplayFormat("dd/MM/yyyy")
        self._from_edit.setCalendarPopup(True)
        self._from_edit.setDate(QDate.currentDate().addMonths(-1))
        self._from_edit.setFixedHeight(30)
        self._from_edit.setMaximumWidth(130)
        custom_layout.addWidget(self._from_edit)

        custom_layout.addWidget(QLabel("To:"))
        self._to_edit = QDateEdit()
        self._to_edit.setDisplayFormat("dd/MM/yyyy")
        self._to_edit.setCalendarPopup(True)
        self._to_edit.setDate(QDate.currentDate())
        self._to_edit.setFixedHeight(30)
        self._to_edit.setMaximumWidth(130)
        custom_layout.addWidget(self._to_edit)

        apply_btn = QPushButton("Apply")
        apply_btn.setObjectName("primary")
        apply_btn.setFixedHeight(30)
        apply_btn.setFixedWidth(70)
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.clicked.connect(self._apply_custom)
        custom_layout.addWidget(apply_btn)
        custom_layout.addStretch()

        root.addWidget(self._custom_row)

        # ── Signals ────────────────────────────────────────────────────────
        for name, btn in self._preset_btns.items():
            btn.clicked.connect(lambda checked, n=name: self._on_preset(n))

        # Default selection
        self._preset_btns["All Time"].setChecked(True)

    def _on_preset(self, name: str):
        if name == "Custom":
            self._custom_row.setVisible(True)
            # Don't emit yet — wait for Apply
        else:
            self._custom_row.setVisible(False)
            df, dt = _preset_range(name)
            self._date_from, self._date_to = df, dt
            self.changed.emit(df, dt)

    def _apply_custom(self):
        qf = self._from_edit.date()
        qt = self._to_edit.date()
        df = f"{qf.year():04d}-{qf.month():02d}-{qf.day():02d}"
        dt = f"{qt.year():04d}-{qt.month():02d}-{qt.day():02d}"
        self._date_from, self._date_to = df, dt
        self.changed.emit(df, dt)

    def current_range(self) -> tuple[str, str]:
        return self._date_from, self._date_to


# ── Summary strip ──────────────────────────────────────────────────────────────

class PeriodSummaryStrip(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {CARD};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
        """)
        self.setFixedHeight(52)

        row = QHBoxLayout(self)
        row.setContentsMargins(20, 0, 20, 0)
        row.setSpacing(0)

        def stat(icon: str, title: str, color: str):
            cell = QHBoxLayout()
            cell.setSpacing(10)
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(f"font-size: 16px; border: none; background: transparent;")
            cell.addWidget(icon_lbl)
            right = QVBoxLayout()
            right.setSpacing(0)
            t = QLabel(title)
            t.setStyleSheet(f"color: {SUBTEXT}; font-size: 10px; font-weight: 600; border: none; background: transparent;")
            v = QLabel("—")
            v.setStyleSheet(f"color: {color}; font-size: 15px; font-weight: 700; border: none; background: transparent;")
            right.addWidget(t)
            right.addWidget(v)
            cell.addLayout(right)
            return cell, v

        inc_row, self._income_val   = stat("↑", "INCOME",   GREEN)
        exp_row, self._expense_val  = stat("↓", "EXPENSES", RED)
        net_row, self._net_val      = stat("≈", "NET",      TEXT)

        def sep():
            f = QFrame()
            f.setFrameShape(QFrame.Shape.VLine)
            f.setStyleSheet(f"color: {BORDER}; background: transparent;")
            return f

        row.addLayout(inc_row)
        row.addSpacing(24)
        row.addWidget(sep())
        row.addSpacing(24)
        row.addLayout(exp_row)
        row.addSpacing(24)
        row.addWidget(sep())
        row.addSpacing(24)
        row.addLayout(net_row)
        row.addStretch()

    def update(self, date_from: str, date_to: str):
        s = db.get_period_summary(date_from or None, date_to or None)
        net = s["income"] - s["expenses"]
        net_color = GREEN if net >= 0 else RED
        self._income_val.setText(f"€{s['income']:,.2f}")
        self._expense_val.setText(f"€{s['expenses']:,.2f}")
        self._net_val.setText(f"{'+'if net>=0 else '−'}€{abs(net):,.2f}")
        self._net_val.setStyleSheet(
            f"color: {net_color}; font-size: 15px; font-weight: 700; border: none; background: transparent;"
        )


# ── Chart 1: Grouped bar — Income vs Expenses ─────────────────────────────────

class IncomeExpenseChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        self.fig = Figure(figsize=(9, 4.5), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.canvas)

    def refresh(self, date_from: str = "", date_to: str = ""):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        _setup_ax(self.fig, ax)

        # Auto-choose grouping: day if ≤ 60 days, else month
        days = _days_in_range(date_from, date_to)
        group_by = "day" if days <= 60 else "month"
        rows = db.get_grouped_totals(date_from or None, date_to or None, group_by)

        if not rows:
            _no_data(ax)
            self.canvas.draw()
            return

        labels   = [r["period"]   for r in rows]
        incomes  = [r["income"]   for r in rows]
        expenses = [r["expenses"] for r in rows]
        short    = [_label_period(lbl, group_by) for lbl in labels]

        x = np.arange(len(labels))
        w = 0.36

        bars_i = ax.bar(x - w/2, incomes,  w, label="Income",   color=GREEN, alpha=0.88, zorder=3)
        bars_e = ax.bar(x + w/2, expenses, w, label="Expenses",  color=RED,   alpha=0.88, zorder=3)

        max_val = max(max(incomes + expenses, default=1), 1)
        for bar in list(bars_i) + list(bars_e):
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h + max_val * 0.012,
                        f"€{h:,.0f}", ha="center", va="bottom", fontsize=8, color=SUBTEXT)

        ax.set_xticks(x)
        ax.set_xticklabels(short, fontsize=9)
        ax.set_ylabel("Amount (€)", color=SUBTEXT, labelpad=10)
        ax.legend()
        ax.margins(x=0.04)
        ax.grid(axis="y", zorder=0)
        ax.set_axisbelow(True)
        self.canvas.draw()


# ── Chart 2: Spending by Tag (donut) ──────────────────────────────────────────

class SpendingByTagChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        self.fig = Figure(figsize=(8, 4.5), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.canvas)

    def refresh(self, date_from: str = "", date_to: str = ""):
        self.fig.clear()
        data = db.get_spending_by_tag(date_from or None, date_to or None)

        if not data:
            ax = self.fig.add_subplot(111)
            _no_data(ax, "No expense data for this period.")
            self.canvas.draw()
            return

        gs = self.fig.add_gridspec(1, 2, width_ratios=[1.2, 1])
        ax_donut = self.fig.add_subplot(gs[0])
        ax_leg   = self.fig.add_subplot(gs[1])
        self.fig.patch.set_facecolor(SURFACE)
        ax_donut.set_facecolor(SURFACE)
        ax_leg.set_facecolor(SURFACE)
        ax_leg.axis("off")

        labels = [row[0] for row in data[:10]]
        values = [row[1] for row in data[:10]]
        colors = CHART_COLORS[:len(labels)]
        total  = sum(values)

        _, _, autotexts = ax_donut.pie(
            values, labels=None,
            autopct=lambda pct: f"{pct:.1f}%" if pct > 4 else "",
            startangle=140, colors=colors,
            wedgeprops={"width": 0.55, "edgecolor": SURFACE, "linewidth": 2},
            pctdistance=0.78,
        )
        for at in autotexts:
            at.set_color(BG)
            at.set_fontsize(9)
            at.set_fontweight("bold")

        ax_donut.text(0,     0,    f"€{total:,.0f}", ha="center", va="center",
                      fontsize=14, fontweight="bold", color=TEXT)
        ax_donut.text(0, -0.18, "total spent", ha="center", va="center",
                      fontsize=9, color=SUBTEXT)

        for i, (label, val, color) in enumerate(zip(labels, values, colors)):
            y = 0.95 - i * 0.10
            ax_leg.add_patch(plt.Rectangle((0, y - 0.03), 0.04, 0.07, color=color,
                                            transform=ax_leg.transAxes, clip_on=False))
            ax_leg.text(0.10, y + 0.01, label, transform=ax_leg.transAxes,
                        va="center", fontsize=10, color=TEXT)
            pct = val / total * 100
            ax_leg.text(0.99, y + 0.01, f"€{val:,.2f}  ({pct:.1f}%)",
                        transform=ax_leg.transAxes, va="center", ha="right",
                        fontsize=9, color=SUBTEXT)

        self.canvas.draw()


# ── Chart 3: Balance over time (line) ─────────────────────────────────────────

class BalanceTrendChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        self.fig = Figure(figsize=(9, 4.5), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.canvas)

    def refresh(self, date_from: str = "", date_to: str = ""):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        _setup_ax(self.fig, ax)

        rows = db.get_balance_over_time(date_from or None, date_to or None)
        if not rows:
            _no_data(ax)
            self.canvas.draw()
            return

        dates    = [r["date"]    for r in rows]
        balances = [r["balance"] for r in rows]
        x        = list(range(len(dates)))

        ax.plot(x, balances, color=BLUE, linewidth=2.5, zorder=4)
        ax.fill_between(x, balances, 0, where=[b >= 0 for b in balances],
                         alpha=0.15, color=GREEN, zorder=3)
        ax.fill_between(x, balances, 0, where=[b <  0 for b in balances],
                         alpha=0.15, color=RED,   zorder=3)
        ax.axhline(0, color=BORDER, linewidth=1, zorder=2)

        last_bal   = balances[-1]
        bal_color  = GREEN if last_bal >= 0 else RED
        ax.annotate(
            f"€{last_bal:,.2f}",
            xy=(x[-1], last_bal),
            xytext=(-60, 15 if last_bal >= 0 else -25),
            textcoords="offset points",
            fontsize=11, fontweight="bold", color=bal_color,
            arrowprops={"arrowstyle": "->", "color": bal_color, "lw": 1.5},
        )

        n    = len(x)
        step = max(1, n // 8)
        tick_x = x[::step]
        tick_labels = []
        for i in tick_x:
            try:
                dt = datetime.strptime(dates[i], "%Y-%m-%d")
                tick_labels.append(dt.strftime("%d/%m/%y"))
            except Exception:
                tick_labels.append(dates[i])

        ax.set_xticks(tick_x)
        ax.set_xticklabels(tick_labels, rotation=30, ha="right")
        ax.set_ylabel("Balance (€)", color=SUBTEXT, labelpad=10)
        ax.margins(x=0.02)
        self.canvas.draw()


# ── ChartsView ─────────────────────────────────────────────────────────────────

class ChartsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(16)

        # Header
        title = QLabel("Charts & Analytics")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        # Period picker
        self._picker = PeriodPicker()
        root.addWidget(self._picker)

        # Summary strip
        self._summary = PeriodSummaryStrip()
        root.addWidget(self._summary)

        # Tabs
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        self._chart_bar    = IncomeExpenseChart()
        self._chart_donut  = SpendingByTagChart()
        self._chart_trend  = BalanceTrendChart()

        self.tabs.addTab(self._chart_bar,   "📊  Income vs Expenses")
        self.tabs.addTab(self._chart_donut, "🍩  Spending by Tag")
        self.tabs.addTab(self._chart_trend, "📈  Balance Trend")

        # Signals
        self._picker.changed.connect(self._on_period_changed)
        self.tabs.currentChanged.connect(self._on_tab_change)

        # Initial load
        self._date_from = ""
        self._date_to   = ""
        self._refresh_current()
        self._summary.update("", "")

    # ── Slots ──────────────────────────────────────────────────────────────────

    def _on_period_changed(self, date_from: str, date_to: str):
        self._date_from = date_from
        self._date_to   = date_to
        self._summary.update(date_from, date_to)
        self._refresh_current()

    def _on_tab_change(self, _idx: int):
        self._refresh_current()

    def _refresh_current(self):
        w = self.tabs.currentWidget()
        if hasattr(w, "refresh"):
            w.refresh(self._date_from, self._date_to)

    # ── Public ─────────────────────────────────────────────────────────────────

    def refresh(self):
        """Called when navigating to this page."""
        self._summary.update(self._date_from, self._date_to)
        self._refresh_current()

    def refresh_all_tabs(self):
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if hasattr(w, "refresh"):
                w.refresh(self._date_from, self._date_to)
