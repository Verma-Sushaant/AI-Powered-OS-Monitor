import psutil
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import pyqtgraph as pg
import time

class MemoryWorker(QThread):
    data_updated = pyqtSignal(float, dict)
    def __init__(self):
        super().__init__()
        self.total_mem = psutil.virtual_memory().total / (1024 ** 3)
    def run(self):
        while True:
            mem = psutil.virtual_memory()
            details = {
                'total': self.total_mem,
                'available': mem.available / (1024 ** 3),
                'used': mem.used / (1024 ** 3),
                'free': mem.free / (1024 ** 3),
                'percent': mem.percent,
            }
            self.data_updated.emit(mem.percent, details)
            time.sleep(1)

class MemoryMonitorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.mem_usage_data = [0] * 60

        self.worker_thread = MemoryWorker()
        self.worker_thread.data_updated.connect(self.update_display)
        self.worker_thread.start()

        layout = QGridLayout(self)

        top_label = QHBoxLayout()
        self.left_label = QLabel("Memory")
        self.left_label.setStyleSheet("color: white; font-size: 20pt;")
        self.right_label = QLabel(f"{round(self.worker_thread.total_mem):.1f} GB")
        self.right_label.setStyleSheet("color: white; font-size: 12pt;")
        top_label.addWidget(self.left_label, alignment=Qt.AlignLeft)
        top_label.addWidget(self.right_label, alignment=Qt.AlignRight)
        layout.addLayout(top_label, 0, 0, 1, 2)

        # Top labels
        top_labels = QHBoxLayout()
        self.top_left_label = QLabel("Memory Usage")
        self.top_left_label.setStyleSheet("color: white; font-size: 8pt;")
        self.top_right_label = QLabel(f"{self.worker_thread.total_mem:.1f} GB")
        self.top_right_label.setStyleSheet("color: white; font-size: 8pt;")
        top_labels.addWidget(self.top_left_label, alignment=Qt.AlignLeft)
        top_labels.addWidget(self.top_right_label, alignment=Qt.AlignRight)
        layout.addLayout(top_labels, 1, 0, 1, 2)

        # Plot setup
        self.mem_plot = pg.PlotWidget()
        self.mem_plot.setBackground('#1C1C1C')
        self.mem_plot.getPlotItem().showGrid(x=True, y=True, alpha=0.7)
        self.mem_plot.getPlotItem().showAxis('top', True)
        self.mem_plot.getPlotItem().showAxis('right', True)
        self.mem_plot.getPlotItem().getAxis('bottom').setTicks([])
        self.mem_plot.getPlotItem().getAxis('left').setTicks([])
        self.mem_plot.getPlotItem().getAxis('top').setTicks([])
        self.mem_plot.getPlotItem().getAxis('right').setTicks([])
        self.mem_plot.setYRange(0, 100)
        self.mem_plot.setMouseEnabled(x=False, y=False)
        self.mem_plot.setMenuEnabled(False)
        self.mem_plot.getPlotItem().hideButtons()
        self.mem_curve = self.mem_plot.plot(pen=pg.mkPen('#8A2BE2', width=2), fillLevel=0, brush=(138, 43, 226, 80))
        self.mem_plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mem_plot.setMinimumHeight(300)
        self.mem_plot.setMinimumWidth(600)
        layout.addWidget(self.mem_plot, 2, 0, 1, 2)

        # Bottom X-axis labels
        x_label_layout = QHBoxLayout()
        self.left_x_label = QLabel("60 seconds")
        self.left_x_label.setStyleSheet("color: #E0E0E0; font-size: 8pt;")
        self.right_x_label = QLabel("0")
        self.right_x_label.setStyleSheet("color: #E0E0E0; font-size: 8pt;")
        x_label_layout.addWidget(self.left_x_label, alignment=Qt.AlignLeft)
        x_label_layout.addWidget(self.right_x_label, alignment=Qt.AlignRight)
        layout.addLayout(x_label_layout, 3, 0, 1, 2)

        # Details label
        self.details_label = QLabel()
        self.details_label.setStyleSheet("color: #E0E0E0; font-size: 9pt;")
        self.details_label.setWordWrap(True)
        layout.addWidget(self.details_label, 4, 0, 1, 2)

        layout.setRowStretch(0, 0)   
        layout.setRowStretch(1, 0)  
        layout.setRowStretch(2, 8)  
        layout.setRowStretch(3, 0)   
        layout.setRowStretch(4, 0)

    def update_display(self, percent, details):
        self.mem_usage_data = self.mem_usage_data[1:] + [percent]
        self.mem_curve.setData(self.mem_usage_data)

        details_str = (
            f"<b>Total:</b> {details['total']:.2f} GB<br>"
            f"<b>Available:</b> {details['available']:.2f} GB<br>"
            f"<b>Used:</b> {details['used']:.2f} GB<br>"
            f"<b>Free:</b> {details['free']:.2f} GB<br>"
            f"<b>Usage Percent:</b> {details['percent']}%"
        )
        self.details_label.setText(details_str)

    def closeEvent(self, event):
        self.worker_thread.terminate()
        self.worker_thread.wait()
        event.accept()