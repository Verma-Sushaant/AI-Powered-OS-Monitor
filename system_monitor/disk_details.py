import psutil
import time
import wmi
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import pyqtgraph as pg


class DiskMonitorThread(QThread):
    update_signal = pyqtSignal(float, float, float, float)  # active, read, write, transfer in MB/s

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.prev_disk = psutil.disk_io_counters()
        self.prev_time = time.time()

    def run(self):
        while self.running:
            curr_disk = psutil.disk_io_counters()
            interval = time.time() - self.prev_time

            read_speed = (curr_disk.read_bytes - self.prev_disk.read_bytes) / interval / (1024 * 1024) if interval > 0 else 0
            write_speed = (curr_disk.write_bytes - self.prev_disk.write_bytes) / interval / (1024 * 1024) if interval > 0 else 0
            transfer_rate = read_speed + write_speed

            MAX_DISK_MBPS = 5000
            read_delta = curr_disk.read_bytes - self.prev_disk.read_bytes
            write_delta = curr_disk.write_bytes - self.prev_disk.write_bytes
            interval = time.time() - self.prev_time
            if interval == 0:
                interval = 1

            read_speed = read_delta / interval / (1024 * 1024)
            write_speed = write_delta / interval / (1024 * 1024)
            transfer_rate = read_speed + write_speed

            # Simulated Active Time as % of MAX speed
            active_time = min((transfer_rate / MAX_DISK_MBPS) * 100, 100)


            self.prev_disk = curr_disk
            self.prev_time = time.time()

            self.update_signal.emit(active_time, read_speed, write_speed, transfer_rate)
            self.msleep(1000)


    def stop(self):
        self.running = False
        self.quit()
        self.wait()
        self.deleteLater()


class DiskMonitorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.disk = wmi.WMI().Win32_DiskDrive()[0]

        self.active_data = [0] * 60
        self.transfer_data = [0] * 60
        self.x_start = 0

        layout = QGridLayout(self)

        # === Top Labels ===
        top_label = QHBoxLayout()
        self.left_label = QLabel("Disk")
        self.left_label.setStyleSheet("color: white; font-size: 20pt;")
        self.right_label = QLabel(self.disk.Model)
        self.right_label.setStyleSheet("color: white; font-size: 12pt;")
        top_label.addWidget(self.left_label, alignment=Qt.AlignLeft)
        top_label.addWidget(self.right_label, alignment=Qt.AlignRight)
        layout.addLayout(top_label, 0, 0, 1, 2)

        # === Active Time Plot ===
        top_labels_layout = QHBoxLayout()
        self.top_left_label = QLabel("Active Time")
        self.top_left_label.setStyleSheet("color: white; font-size: 8pt;")
        self.top_right_label = QLabel("100%")
        self.top_right_label.setStyleSheet("color: white; font-size: 8pt;")
        top_labels_layout.addWidget(self.top_left_label, alignment=Qt.AlignLeft)
        top_labels_layout.addWidget(self.top_right_label, alignment=Qt.AlignRight)
        layout.addLayout(top_labels_layout, 1, 0, 1, 2)

        self.active_plot = pg.PlotWidget()
        self.active_plot.setBackground('#1C1C1C')
        self.active_plot.setYRange(0, 100)
        self.active_plot.setMouseEnabled(x=False, y=False)
        self.active_plot.setMenuEnabled(False)
        self.active_plot.getPlotItem().showGrid(x=True, y=True, alpha=0.7)
        for axis in ['bottom', 'left', 'top', 'right']:
            self.active_plot.getPlotItem().showAxis(axis, True)
            self.active_plot.getPlotItem().getAxis(axis).setTicks([])
        self.active_curve = self.active_plot.plot(pen=pg.mkPen('#00FF7F', width=2), fillLevel=0, brush=(0, 255, 127, 80))
        self.active_plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.active_plot.setMinimumHeight(200)
        layout.addWidget(self.active_plot, 2, 0, 1, 2)

        x_label_layout = QHBoxLayout()
        self.left_label = QLabel("60 seconds")
        self.left_label.setStyleSheet("color: #E0E0E0; font-size: 8pt;")
        self.right_label = QLabel("0")
        self.right_label.setStyleSheet("color: #E0E0E0; font-size: 8pt;")
        x_label_layout.addWidget(self.left_label, alignment=Qt.AlignLeft)
        x_label_layout.addWidget(self.right_label, alignment=Qt.AlignRight)
        layout.addLayout(x_label_layout, 3, 0, 1, 2)

        x_label_layout = QHBoxLayout()
        self.transfer_label = QLabel("Disk transfer rate")
        self.transfer_label.setStyleSheet("color: #E0E0E0; font-size: 8pt;")
        self.transfer_rate_label = QLabel()
        self.transfer_rate_label.setStyleSheet("color: #E0E0E0; font-size: 8pt;")
        x_label_layout.addWidget(self.transfer_label, alignment=Qt.AlignLeft)
        x_label_layout.addWidget(self.transfer_rate_label, alignment=Qt.AlignRight)
        layout.addLayout(x_label_layout, 4, 0, 1, 2)


        # === Transfer Rate Plot ===
        self.transfer_plot = pg.PlotWidget()
        self.transfer_plot.setBackground('#1C1C1C')
        self.transfer_plot.setMouseEnabled(x=False, y=False)
        self.transfer_plot.setMenuEnabled(False)
        self.transfer_plot.getPlotItem().showGrid(x=True, y=True, alpha=0.7)
        for axis in ['bottom', 'left', 'top', 'right']:
            self.transfer_plot.getPlotItem().showAxis(axis, True)
            self.transfer_plot.getPlotItem().getAxis(axis).setTicks([])
        self.transfer_curve = self.transfer_plot.plot(pen=pg.mkPen('#1E90FF', width=2), fillLevel=0, brush=(30, 144, 255, 80))
        self.transfer_plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.transfer_plot.setMinimumHeight(150)
        layout.addWidget(self.transfer_plot, 5, 0, 1, 2)

        # === Bottom X-axis Label ===
        x_label_layout = QHBoxLayout()
        self.left_label = QLabel("60 seconds")
        self.left_label.setStyleSheet("color: #E0E0E0; font-size: 8pt;")
        self.right_label = QLabel("0")
        self.right_label.setStyleSheet("color: #E0E0E0; font-size: 8pt;")
        x_label_layout.addWidget(self.left_label, alignment=Qt.AlignLeft)
        x_label_layout.addWidget(self.right_label, alignment=Qt.AlignRight)
        layout.addLayout(x_label_layout, 6, 0, 1, 2)

        # === Disk Info Label ===
        self.details_label = QLabel()
        self.details_label.setStyleSheet("color: #E0E0E0; font-size: 10pt;")
        self.details_label.setWordWrap(True)
        layout.addWidget(self.details_label, 7, 0, 1, 2)

        layout.setRowStretch(0, 0)
        layout.setRowStretch(1, 0)
        layout.setRowStretch(2, 8)
        layout.setRowStretch(3, 0)
        layout.setRowStretch(4, 0)
        layout.setRowStretch(5, 4)

        self.monitor_thread = DiskMonitorThread()
        self.monitor_thread.update_signal.connect(self.update_stats)
        self.monitor_thread.start()

    def update_stats(self, active_time, read_speed, write_speed, transfer_rate):
        # Dynamically adjust unit
        if transfer_rate < 1.0:
            rate_display = f"{transfer_rate * 1024:.0f} KB/s"
            graph_rate_value = transfer_rate * 1024  # Show in KB/s
            self.transfer_plot.setYRange(0, 1024)
        else:
            rate_display = f"{transfer_rate:.2f} MB/s"
            graph_rate_value = transfer_rate  # Show in MB/s
            self.transfer_plot.setYRange(0, 10)

        # Update data
        self.active_data = self.active_data[1:] + [active_time]
        self.transfer_data = self.transfer_data[1:] + [graph_rate_value]
        x_values = list(range(len(self.active_data)))

        self.active_curve.setData(x=x_values, y=self.active_data)
        self.transfer_curve.setData(x=x_values, y=self.transfer_data)

        # Update label
        self.transfer_rate_label.setText(rate_display)

        read_display = f"{read_speed * 1024:.0f} KB/s" if read_speed < 1 else f"{read_speed:.2f} MB/s"
        write_display = f"{write_speed * 1024:.0f} KB/s" if write_speed < 1 else f"{write_speed:.2f} MB/s"

        details = (
            f"<b>Active Time:</b> {active_time:.2f}%<br>"
            f"<b>Read Speed:</b> {read_display}<br>"
            f"<b>Write Speed:</b> {write_display}<br>"
            f"<b>Capacity:</b> {int(self.disk.Size) / (1024 * 1024 * 1024):.2f} GB"
        )
        self.details_label.setText(details)

    def closeEvent(self, event):
        self.monitor_thread.stop()
        event.accept()