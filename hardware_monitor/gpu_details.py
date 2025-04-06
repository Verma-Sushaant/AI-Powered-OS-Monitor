import GPUtil
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import pyqtgraph as pg
import time

class GPUWorker(QThread):
    gpu_data_updated = pyqtSignal(float, float, dict)

    def run(self):
        self.running = True
        while self.running:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                load = gpu.load * 100
                mem_percent = (gpu.memoryUsed / gpu.memoryTotal) * 100

                details = {
                    "name": gpu.name,
                    "temp": gpu.temperature,
                    "load": load,
                    "mem_used": gpu.memoryUsed/1024,
                    "mem_total": gpu.memoryTotal/1024,
                    "driver": gpu.driver,
                }
                self.gpu_data_updated.emit(load, mem_percent, details)
            time.sleep(1)

    def stop(self):
        self.running = False
        self.quit()
        self.wait()
        self.deleteLater()

class GPUMonitorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.gpu_usage_data = [0] * 60
        self.gpu_mem_data = [0] * 60

        layout = QGridLayout(self)

        # Top Title
        title_layout = QHBoxLayout()
        self.left_label = QLabel("GPU")
        self.left_label.setStyleSheet("color: white; font-size: 20pt;")
        self.right_label = QLabel("NVIDIA / AMD")
        self.right_label.setStyleSheet("color: white; font-size: 12pt;")
        title_layout.addWidget(self.left_label, alignment=Qt.AlignLeft)
        title_layout.addWidget(self.right_label, alignment=Qt.AlignRight)
        layout.addLayout(title_layout, 0, 0, 1, 2)

        # Top plot labels
        top_labels_layout = QHBoxLayout()
        self.top_left_label = QLabel("GPU Load")
        self.top_left_label.setStyleSheet("color: white; font-size: 8pt;")
        self.top_right_label = QLabel("100%")
        self.top_right_label.setStyleSheet("color: white; font-size: 8pt;")
        top_labels_layout.addWidget(self.top_left_label, alignment=Qt.AlignLeft)
        top_labels_layout.addWidget(self.top_right_label, alignment=Qt.AlignRight)
        layout.addLayout(top_labels_layout, 1, 0, 1, 2)

        # GPU Load Plot
        self.gpu_plot = pg.PlotWidget()
        self.gpu_plot.setBackground('#1C1C1C')
        self.gpu_plot.getPlotItem().showGrid(x=True, y=True, alpha=0.7)
        self.gpu_plot.getPlotItem().showAxis('top', True)
        self.gpu_plot.getPlotItem().showAxis('right', True)
        for axis in ['bottom', 'left', 'top', 'right']:
            self.gpu_plot.getPlotItem().getAxis(axis).setTicks([])
        self.gpu_plot.setYRange(0, 100)
        self.gpu_plot.setMouseEnabled(x=False, y=False)
        self.gpu_plot.setMenuEnabled(False)
        self.gpu_plot.getPlotItem().hideButtons()
        self.gpu_curve = self.gpu_plot.plot(pen=pg.mkPen('#FF8C00', width=2), fillLevel=0, brush=(255, 140, 0, 80))
        self.gpu_plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.gpu_plot.setMinimumHeight(300)
        layout.addWidget(self.gpu_plot, 2, 0, 1, 2)

        # Bottom plot X-labels
        bottom_label_layout = QHBoxLayout()
        self.bottom_left_label = QLabel("60 seconds")
        self.bottom_left_label.setStyleSheet("color: #E0E0E0; font-size: 8pt;")
        self.bottom_right_label = QLabel("0")
        self.bottom_right_label.setStyleSheet("color: #E0E0E0; font-size: 8pt;")
        bottom_label_layout.addWidget(self.bottom_left_label, alignment=Qt.AlignLeft)
        bottom_label_layout.addWidget(self.bottom_right_label, alignment=Qt.AlignRight)
        layout.addLayout(bottom_label_layout, 3, 0, 1, 2)

        top_labels_layout = QHBoxLayout()
        self.top_left_label = QLabel("GPU memory usage")
        self.top_left_label.setStyleSheet("color: white; font-size: 8pt;")
        self.top_right_label = QLabel(str(GPUtil.getGPUs()[0].memoryTotal/1024)+" GB")
        self.top_right_label.setStyleSheet("color: white; font-size: 8pt;")
        top_labels_layout.addWidget(self.top_left_label, alignment=Qt.AlignLeft)
        top_labels_layout.addWidget(self.top_right_label, alignment=Qt.AlignRight)
        layout.addLayout(top_labels_layout, 4, 0, 1, 2)

        # GPU Memory Plot
        self.gpu_mem_plot = pg.PlotWidget()
        self.gpu_mem_plot.setBackground('#1C1C1C')
        self.gpu_mem_plot.getPlotItem().showGrid(x=True, y=True, alpha=0.7)
        self.gpu_mem_plot.getPlotItem().showAxis('top', True)
        self.gpu_mem_plot.getPlotItem().showAxis('right', True)
        for axis in ['bottom', 'left', 'top', 'right']:
            self.gpu_mem_plot.getPlotItem().getAxis(axis).setTicks([])
        self.gpu_mem_plot.setYRange(0, 100)
        self.gpu_mem_plot.setMouseEnabled(x=False, y=False)
        self.gpu_mem_plot.setMenuEnabled(False)
        self.gpu_mem_plot.getPlotItem().hideButtons()
        self.gpu_mem_curve = self.gpu_mem_plot.plot(pen=pg.mkPen('#00CED1', width=2), fillLevel=0, brush=(0, 206, 209, 80))
        self.gpu_mem_plot.setMinimumHeight(200)
        layout.addWidget(self.gpu_mem_plot, 5, 0, 1, 2)

        # Details label
        self.details_label = QLabel()
        self.details_label.setStyleSheet("color: #E0E0E0; font-size: 9pt;")
        self.details_label.setWordWrap(True)
        layout.addWidget(self.details_label, 6, 0, 1, 2)

        layout.setRowStretch(0, 0)
        layout.setRowStretch(1, 0)
        layout.setRowStretch(2, 10)
        layout.setRowStretch(3, 0)
        layout.setRowStretch(4, 0)
        layout.setRowStretch(5, 5)
        layout.setRowStretch(6, 0)

        # Worker
        self.worker = GPUWorker()
        self.worker.gpu_data_updated.connect(self.update_graph_and_info)
        self.worker.start()

    def update_graph_and_info(self, load, mem_percent, details):
        self.gpu_usage_data = self.gpu_usage_data[1:] + [load]
        self.gpu_mem_data = self.gpu_mem_data[1:] + [mem_percent]

        self.gpu_curve.setData(self.gpu_usage_data)
        self.gpu_mem_curve.setData(self.gpu_mem_data)

        self.right_label.setText(details["name"])

        details_str = (
            f"<b>Load:</b> {details['load']:.2f}%<br>"
            f"<b>Temperature:</b> {details['temp']}°C<br>"
            f"<b>Memory Used:</b> {details['mem_used']} / {details['mem_total']} GB<br>"
            f"<b>Driver:</b> {details['driver']}"
        )
        self.details_label.setText(details_str)

    def closeEvent(self, event):
        self.worker.stop()
        super().closeEvent(event)
