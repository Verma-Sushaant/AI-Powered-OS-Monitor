from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget,
    QVBoxLayout, QSizePolicy, QPushButton, QHBoxLayout,
    QLabel, QFrame, QSpacerItem, QGraphicsDropShadowEffect, QGraphicsBlurEffect
)
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QRect, QTimer, QEasingCurve, QSize
from PyQt5.QtGui import QColor, QIcon
import sys
import os
import psutil
import pyqtgraph as pg

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from system_monitor.cpu_details import CPUMonitorWidget
from system_monitor.memory_details import MemoryMonitorWidget
from system_monitor.disk_details import DiskMonitorWidget
from hardware_monitor.network_details import NetworkMonitorWidget
from hardware_monitor.gpu_details import GPUMonitorWidget

pg.setConfigOption('background', '#121212')
pg.setConfigOption('foreground', 'white')
pg.setConfigOptions(antialias=True)


class Overlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.full_width = 500
        self.full_height = 600
        self.setFixedSize(self.full_width, self.full_height)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Background Frosted Glass + Glow
        self.blur_background = QFrame(self)
        self.blur_background.setGeometry(0, 0, self.full_width, self.full_height)
        self.blur_background.setStyleSheet("background-color: rgba(255, 255, 255, 25); border-radius: 18px;")

        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(40)
        self.blur_background.setGraphicsEffect(blur)

        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(40)
        glow.setOffset(0, 0)
        glow.setColor(QColor(0, 206, 209, 80))
        self.setGraphicsEffect(glow)

        # Container inside blurred background
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, self.full_width, self.full_height)
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(40, 40, 40, 200);
                border-radius: 18px;
                border: 2px solid #00CED1;
            }
        """)

        container_glow = QGraphicsDropShadowEffect()
        container_glow.setBlurRadius(60)
        container_glow.setOffset(0, 0)
        container_glow.setColor(QColor(0, 206, 209, 140))
        self.container.setGraphicsEffect(container_glow)

        # Layout inside container
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(12, 12, 12, 12)

        # Close button
        close_btn_layout = QHBoxLayout()
        close_btn_layout.addStretch()
        close_btn = QPushButton("✖")
        close_btn.setFixedSize(26, 26)
        close_btn.clicked.connect(self.animate_hide)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #00CED1;
                color: black;
                border-radius: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00B4B8;
                color: white;
            }
        """)
        close_btn_layout.addWidget(close_btn)
        container_layout.addLayout(close_btn_layout)

        # Title
        title_label = QLabel("No new notifications") #🤖 AI Module Panel
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        container_layout.addWidget(title_label)

        # Placeholder content
        container_layout.addWidget(QPushButton("Clear")) #AI Placeholder Button

        self.opacity_anim = None
        self.slide_anim = None

    def snap_to_corner(self):
        if self.parent_window:
            parent_geo = self.parent_window.geometry()
            self.target_x = parent_geo.x() + parent_geo.width() - self.full_width - 20
            self.target_y = parent_geo.y() + 60

    def animate_hide(self):
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(500)  # slower
        self.opacity_anim.setStartValue(1.0)
        self.opacity_anim.setEndValue(0.0)

        self.slide_anim = QPropertyAnimation(self, b"pos")
        self.slide_anim.setDuration(500)  # slower
        self.slide_anim.setStartValue(self.pos())
        self.slide_anim.setEndValue(QPoint(self.x() + self.full_width + 20, self.y()))
        self.slide_anim.setEasingCurve(QEasingCurve.InBack)

        self.opacity_anim.finished.connect(self.hide)
        self.opacity_anim.start()
        self.slide_anim.start()

    def show_with_animation(self):
        self.snap_to_corner()

        start_x = self.target_x + self.full_width + 20
        self.move(start_x, self.target_y)
        self.setWindowOpacity(0.0)
        self.show()

        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(500)  # slower
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)

        self.slide_anim = QPropertyAnimation(self, b"pos")
        self.slide_anim.setDuration(500)  # slower
        self.slide_anim.setStartValue(QPoint(start_x, self.target_y))
        self.slide_anim.setEndValue(QPoint(self.target_x, self.target_y))
        self.slide_anim.setEasingCurve(QEasingCurve.OutBack)

        self.opacity_anim.start()
        self.slide_anim.start()

    def showEvent(self, event):
        self.snap_to_corner()
        self.setWindowOpacity(1.0)
        self.show_with_animation()
        self.installEventFilter(self.parent_window)

    def eventFilter(self, obj, event):
        if event.type() == event.MouseButtonPress:
            if not self.geometry().contains(event.globalPos()):
                self.animate_hide()
        return super().eventFilter(obj, event)


class SystemMonitorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Monitor")
        self.resize(1366, 1080)

        dark_stylesheet = """
        QWidget {
            background-color: #1C1C1C;
            color: #B2FFFF;
            font-family: 'Segoe UI', sans-serif;
        }

        QTabWidget::pane {
            border: none;
            top: -1px;
            background: #2A2A2A;
            border-radius: 10px;
        }

        QTabBar::tab {
            background: #2A2A2A;
            color: #80F0F2;
            min-width: 120px;
            padding: 8px 24px;
            border: 1px solid #00CED1;
            border-radius: 12px;
            margin: 4px;
            margin-bottom: 2px;
        }

        QTabBar::tab:selected {
            background: #00CED1;
            color: white;
            font-weight: bold;
        }

        QTabBar::tab:hover {
            background: #00B4B8;
        }

        QLabel {
            color: #B2FFFF;
        }

        QPushButton {
            background-color: #00CED1;
            color: #1C1C1C;
            border-radius: 6px;
            padding: 5px;
        }

        QPushButton:hover {
            background-color: #00B4B8;
            color: white;
        }

        QLineEdit, QTextEdit {
            background-color: #2D2D2D;
            color: #B2FFFF;
            border: 1px solid #00CED1;
            border-radius: 4px;
            padding: 4px;
        }

        QLineEdit:focus, QTextEdit:focus {
            border: 1px solid #00CED1;
            outline: none;
        }
        """
        self.setStyleSheet(dark_stylesheet)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        top_bar = QHBoxLayout()
        top_bar.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.button = QPushButton("Notifications")
        self.button.setFixedSize(100, 30)
        self.button.clicked.connect(self.show_panel)
        top_bar.addWidget(self.button)

        self.tabs = QTabWidget()
        self.add_monitor_tab(CPUMonitorWidget, "CPU Monitor")
        self.add_monitor_tab(MemoryMonitorWidget, "Memory")
        self.add_monitor_tab(DiskMonitorWidget, "Disk")
        self.add_monitor_tab(NetworkMonitorWidget, "Network")
        self.add_monitor_tab(GPUMonitorWidget, "GPU Monitor")

        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.tabs)
        self.setCentralWidget(main_widget)

        self.overlay = Overlay(self)
        self.overlay.hide()

    def add_monitor_tab(self, widget_class, title):
        tab = QWidget()
        layout = QVBoxLayout()
        widget = widget_class()
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(widget)
        tab.setLayout(layout)
        self.tabs.addTab(tab, title)

    def show_panel(self):
        if self.overlay.isVisible():
            self.overlay.animate_hide()
        else:
            self.overlay.show_with_animation()


if __name__ == "__main__":
    app = QApplication([])
    window = SystemMonitorApp()
    window.show()
    app.exec_()