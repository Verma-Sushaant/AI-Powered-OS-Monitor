from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QGraphicsDropShadowEffect,
    QPushButton, QHBoxLayout, QLabel
)
from PyQt5.QtCore import Qt, QEasingCurve, QRect, QPropertyAnimation, QTimer
from PyQt5.QtGui import QColor
import psutil


class Overlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.full_width = 500
        self.full_height = 600
        self.setFixedSize(self.full_width, self.full_height)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Container
        self.container = QFrame(self)
        self.container.setStyleSheet("""
            QFrame {
                background-color: #2D2D2D;
                border: 2px solid #00CED1;
                border-radius: 10px;
            }
        """)
        self.container.setGeometry(0, 0, self.full_width, self.full_height)

        # Glow Effect
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(30)
        glow.setOffset(0, 0)
        glow.setColor(QColor(0, 206, 209, 160))
        self.container.setGraphicsEffect(glow)

        container_layout = QVBoxLayout(self.container)

        # Close Button
        close_btn = QPushButton("✖")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.animate_hide)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #00CED1;
                color: black;
                border-radius: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00B4B8;
                color: white;
            }
        """)
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        container_layout.addLayout(close_layout)

        # Title
        container_layout.addWidget(QLabel("🤖 AI Module Panel"))

        # Notification label
        self.notification_label = QLabel("No new notifications")
        self.notification_label.setStyleSheet("color: white;")
        self.notification_label.setWordWrap(True)
        container_layout.addWidget(self.notification_label)

        # Placeholder
        container_layout.addWidget(QPushButton("AI Placeholder Button"))

        # Notification checker timer
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.check_high_usage_processes)
        self.notification_timer.start(5000)  # check every 5 seconds

        self.opacity_anim = None
        self.resize_anim = None

    def snap_to_corner(self):
        if self.parent_window:
            parent_geo = self.parent_window.geometry()
            new_x = parent_geo.x() + parent_geo.width() - self.full_width - 20
            new_y = parent_geo.y() + 60
            self.move(new_x, new_y)

    def animate_hide(self):
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(500)
        self.opacity_anim.setStartValue(1.0)
        self.opacity_anim.setEndValue(0.0)

        self.resize_anim = QPropertyAnimation(self, b"geometry")
        self.resize_anim.setDuration(500)
        self.resize_anim.setStartValue(self.geometry())
        end_rect = QRect(self.x() + self.full_width, self.y(), 0, self.full_height)
        self.resize_anim.setEndValue(end_rect)
        self.resize_anim.setEasingCurve(QEasingCurve.InBack)

        self.opacity_anim.finished.connect(self.hide)
        self.opacity_anim.start()
        self.resize_anim.start()

    def show_with_animation(self):
        self.snap_to_corner()
        start_rect = QRect(self.x() + self.full_width, self.y(), 0, self.full_height)
        end_rect = QRect(self.x(), self.y(), self.full_width, self.full_height)

        self.setGeometry(start_rect)
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self.activateWindow()

        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(500)
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)

        self.resize_anim = QPropertyAnimation(self, b"geometry")
        self.resize_anim.setDuration(500)
        self.resize_anim.setStartValue(start_rect)
        self.resize_anim.setEndValue(end_rect)
        self.resize_anim.setEasingCurve(QEasingCurve.OutBack)

        self.opacity_anim.start()
        self.resize_anim.start()

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

    def check_high_usage_processes(self):
        alerts = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username']):
            try:
                info = proc.info
                if info['username'] and not info['username'].lower().startswith('system'):
                    if info['cpu_percent'] > 75 or info['memory_percent'] > 75:
                        alerts.append(f"⚠️ {info['name']} (PID {info['pid']}) is using {info['cpu_percent']:.1f}% CPU / {info['memory_percent']:.1f}% Memory")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if alerts:
            self.notification_label.setText('\n\n'.join(alerts))
        else:
            self.notification_label.setText("No new notifications")