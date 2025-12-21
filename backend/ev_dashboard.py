import sys
import random
from typing import List

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QProgressBar,
    QGroupBox,
    QSizePolicy,
)
from PyQt5.QtGui import QFont

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class PriceChartCanvas(FigureCanvas):
    """
    Embedded matplotlib chart for 24h price graph.
    Call update_prices(prices) with a list of 24 floats.
    """

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(5, 2))
        super().__init__(self.fig)
        self.setParent(parent)

        self.ax = self.fig.add_subplot(111)
        self.fig.tight_layout(pad=1.2)

        self.ax.set_title("Electricity price (24h)")
        self.ax.set_xlabel("Hour")
        self.ax.set_ylabel("Price")

        # Initial empty plot
        self.hours = list(range(24))
        self.prices = [0] * 24
        (self.line,) = self.ax.plot(self.hours, self.prices, marker="o")
        self.ax.grid(True)

    def update_prices(self, prices: List[float]):
        """
        Update the 24-hour price graph.
        prices must be a list of length 24.
        """
        if not prices or len(prices) != 24:
            return

        self.prices = prices
        self.ax.clear()

        self.ax.set_title("Electricity price (24h)")
        self.ax.set_xlabel("Hour")
        self.ax.set_ylabel("Price")

        # Plot line
        self.ax.plot(self.hours, self.prices, marker="o")
        self.ax.grid(True)

        # Make x-axis ticks 0–23
        self.ax.set_xticks(self.hours)

        self.draw()


class ChargingDashboard(QMainWindow):
    """
    Main EV charging dashboard UI.
    - Mode badge (Price / Load / Manual)
    - Charging status indicator (green / red)
    - 24h price chart
    - Battery % progress bar (enhanced)
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EV Charging Dashboard")
        self.setMinimumSize(1000, 600)

        self._current_mode = "Price"
        self._is_charging = False
        self._battery_percent = 40

        self._build_ui()
        self._apply_styles()

        # Demo timers (you will replace with real updates from your Flask API)
        self._setup_demo_timers()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(16)
        central.setLayout(root_layout)

        # Top area: Left (status + battery) / Right (mode + controls)
        top_layout = QHBoxLayout()
        top_layout.setSpacing(16)

        # Left box: Status & battery
        left_group = QGroupBox("Charging status")
        left_layout = QVBoxLayout()
        left_layout.setSpacing(16)
        left_group.setLayout(left_layout)

        # Status row: text + colored indicator
        status_row = QHBoxLayout()
        status_label_title = QLabel("Status:")
        status_label_title.setObjectName("statusTitle")

        self.status_label = QLabel("Stopped")
        self.status_label.setObjectName("statusLabel")

        # Color indicator box
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(18, 18)
        self.status_indicator.setObjectName("statusIndicator")

        status_row.addWidget(status_label_title)
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        status_row.addWidget(self.status_indicator)

        # Battery group
        battery_group = QGroupBox("Battery")
        battery_layout = QVBoxLayout()
        battery_group.setLayout(battery_layout)

        self.battery_label = QLabel("Battery: 40 %")
        self.battery_label.setObjectName("batteryLabel")

        self.battery_bar = QProgressBar()
        self.battery_bar.setRange(0, 100)
        self.battery_bar.setValue(self._battery_percent)
        self.battery_bar.setFormat("%p%")

        battery_layout.addWidget(self.battery_label)
        battery_layout.addWidget(self.battery_bar)

        left_layout.addLayout(status_row)
        left_layout.addWidget(battery_group)

        # Right box: Mode badge + controls
        right_group = QGroupBox("Control")
        right_layout = QVBoxLayout()
        right_layout.setSpacing(16)
        right_group.setLayout(right_layout)

        # Mode row: Mode label, badge, selector
        mode_row = QHBoxLayout()

        mode_title = QLabel("Mode:")
        mode_title.setObjectName("modeTitle")

        self.mode_badge = QLabel("PRICE")
        self.mode_badge.setObjectName("modeBadge")
        self.mode_badge.setAlignment(Qt.AlignCenter)
        self.mode_badge.setMinimumWidth(90)

        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Price", "Load", "Manual"])
        self.mode_selector.currentTextChanged.connect(self._on_mode_changed)

        mode_row.addWidget(mode_title)
        mode_row.addWidget(self.mode_badge)
        mode_row.addStretch()
        mode_row.addWidget(self.mode_selector)

        # Buttons row: Start / Stop
        buttons_row = QHBoxLayout()
        self.btn_start = QPushButton("Start charging")
        self.btn_stop = QPushButton("Stop charging")

        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_stop.clicked.connect(self._on_stop_clicked)

        buttons_row.addWidget(self.btn_start)
        buttons_row.addWidget(self.btn_stop)
        buttons_row.addStretch()

        right_layout.addLayout(mode_row)
        right_layout.addLayout(buttons_row)
        right_layout.addStretch()

        top_layout.addWidget(left_group, 2)
        top_layout.addWidget(right_group, 1)

        # Bottom: Price chart
        chart_group = QGroupBox("Price overview (24h)")
        chart_layout = QVBoxLayout()
        chart_group.setLayout(chart_layout)

        self.price_chart = PriceChartCanvas(self)
        self.price_chart.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        chart_layout.addWidget(self.price_chart)

        root_layout.addLayout(top_layout, 1)
        root_layout.addWidget(chart_group, 2)

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------
    def _apply_styles(self):
        """
        Stylesheet for glassy / modern look.
        You can tweak colors as you like.
        """
        base_font = QFont("Segoe UI", 10)
        self.setFont(base_font)

        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #050816;
            }

            QWidget {
                color: #E5E7EB;
                font-size: 10pt;
            }

            QGroupBox {
                border: 1px solid #1F2937;
                border-radius: 10px;
                margin-top: 12px;
                background-color: rgba(15, 23, 42, 0.8);
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                color: #9CA3AF;
                font-size: 9pt;
            }

            QLabel#statusTitle,
            QLabel#modeTitle,
            QLabel#batteryLabel {
                color: #9CA3AF;
            }

            QLabel#statusLabel {
                font-weight: 600;
                font-size: 11pt;
            }

            QLabel#modeBadge {
                padding: 4px 10px;
                border-radius: 12px;
                background-color: rgba(59, 130, 246, 0.9);
                color: white;
                font-weight: 600;
                letter-spacing: 1px;
            }

            QPushButton {
                border-radius: 8px;
                padding: 6px 14px;
                background-color: #111827;
                border: 1px solid #1F2937;
            }

            QPushButton:hover {
                background-color: #1F2937;
            }

            QPushButton:pressed {
                background-color: #0F172A;
            }

            QComboBox {
                border-radius: 6px;
                border: 1px solid #1F2937;
                padding: 4px 8px;
                background-color: #020617;
            }

            QProgressBar {
                border: 1px solid #1F2937;
                border-radius: 8px;
                text-align: center;
                background-color: #020617;
                color: #E5E7EB;
                font-weight: 600;
            }

            /* Battery gradient (will be visible inside the chunk) */
            QProgressBar::chunk {
                border-radius: 8px;
                margin: 1px;
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 0,
                    stop: 0 #22C55E,
                    stop: 0.5 #84CC16,
                    stop: 1 #FACC15
                );
            }
            """
        )

        # Status indicator initial color
        self._update_status_indicator()

    # ------------------------------------------------------------------
    # Public API to integrate with your backend logic
    # ------------------------------------------------------------------
    def set_mode(self, mode: str):
        """
        Set and show current mode (Price / Load / Manual).
        You can call this from your backend update logic.
        """
        mode = mode.capitalize()
        if mode not in ["Price", "Load", "Manual"]:
            return

        self._current_mode = mode
        self.mode_badge.setText(mode.upper())

        # Optional: change badge color based on mode
        if mode == "Price":
            bg = "rgba(59, 130, 246, 0.9)"  # blue
        elif mode == "Load":
            bg = "rgba(16, 185, 129, 0.9)"  # teal
        else:  # Manual
            bg = "rgba(234, 179, 8, 0.9)"   # amber

        self.mode_badge.setStyleSheet(
            f"""
            QLabel#modeBadge {{
                padding: 4px 10px;
                border-radius: 12px;
                background-color: {bg};
                color: white;
                font-weight: 600;
                letter-spacing: 1px;
            }}
            """
        )

    def set_charging(self, is_charging: bool):
        """
        Update charging status and color indicator.
        Green = Charging, Red = Stopped.
        """
        self._is_charging = is_charging
        self.status_label.setText("Charging" if is_charging else "Stopped")
        self._update_status_indicator()

    def set_battery_percent(self, value: int):
        """
        Update battery % and progress bar.
        """
        value = max(0, min(100, value))
        self._battery_percent = value
        self.battery_bar.setValue(value)
        self.battery_label.setText(f"Battery: {value} %")

    def update_price_chart(self, prices: List[float]):
        """
        Pass list of 24 values from your /priceperhour endpoint here.
        """
        self.price_chart.update_prices(prices)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _update_status_indicator(self):
        """
        Apply red/green color to the small square indicator.
        """
        color = "#22C55E" if self._is_charging else "#EF4444"
        self.status_indicator.setStyleSheet(
            f"""
            QLabel#statusIndicator {{
                background-color: {color};
                border-radius: 9px;
            }}
            """
        )

    # ------------------------------------------------------------------
    # Handlers for UI controls
    # ------------------------------------------------------------------
    def _on_mode_changed(self, text: str):
        # Local UI update; in your real app you can also notify the backend here.
        self.set_mode(text)

    def _on_start_clicked(self):
        # In your real app: call Flask /start_charge or similar, then update UI.
        self.set_charging(True)

    def _on_stop_clicked(self):
        # In your real app: call Flask /stop_charge or similar, then update UI.
        self.set_charging(False)

    # ------------------------------------------------------------------
    # Demo timers – replace with your real server polling
    # ------------------------------------------------------------------
    def _setup_demo_timers(self):
        """
        Demo only:
        - Randomize battery every 3 seconds
        - Randomize 24h prices every 10 seconds
        Replace this with actual polling of your Flask server.
        """
        self.demo_battery_timer = QTimer(self)
        self.demo_battery_timer.timeout.connect(self._demo_update_battery)
        self.demo_battery_timer.start(3000)

        self.demo_price_timer = QTimer(self)
        self.demo_price_timer.timeout.connect(self._demo_update_prices)
        self.demo_price_timer.start(10000)

    def _demo_update_battery(self):
        # Simple smooth up/down demo
        delta = random.choice([-2, -1, 1, 2])
        self.set_battery_percent(self._battery_percent + delta)

    def _demo_update_prices(self):
        # Generate 24 random values as demo prices
        prices = [round(random.uniform(0.5, 3.0), 2) for _ in range(24)]
        self.update_price_chart(prices)


def main():
    app = QApplication(sys.argv)
    window = ChargingDashboard()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()