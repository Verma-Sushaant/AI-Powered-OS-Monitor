import psutil
import time
import wmi
import subprocess
from PyQt5.QtCore import QObject, QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QHBoxLayout
import pyqtgraph as pg


class NetworkWorker(QObject):
    data_ready = pyqtSignal(float, float, str, str, str)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.running = True
        self.prev_net = psutil.net_io_counters()
        self.prev_time = time.time()

    def get_network_info(self):
        try:
            w = wmi.WMI()
            for nic in w.Win32_NetworkAdapterConfiguration(IPEnabled=True):
                adapter_name = nic.Description
                connection_type = "Wi-Fi" if "wireless" in adapter_name.lower() else "Ethernet"
                ssid = self.get_wifi_ssid() if connection_type == "Wi-Fi" else "N/A"
                return adapter_name, connection_type, ssid
        except Exception:
            return "Unknown Adapter", "Unknown", "N/A"

    def get_wifi_ssid(self):
        try:
            output = subprocess.check_output("netsh wlan show interfaces", shell=True).decode()
            for line in output.splitlines():
                if "SSID" in line and "BSSID" not in line:
                    return line.split(":", 1)[1].strip()
        except Exception:
            return "Unknown"
        return "Not Connected"

    def run(self):
        while self.running:
            curr_net = psutil.net_io_counters()
            interval = time.time() - self.prev_time

            upload = (curr_net.bytes_sent - self.prev_net.bytes_sent) / interval / 1024 * 8 if interval > 0 else 0
            download = (curr_net.bytes_recv - self.prev_net.bytes_recv) / interval / 1024 * 8 if interval > 0 else 0

            self.prev_net = curr_net
            self.prev_time = time.time()

            adapter_name, connection_type, ssid = self.get_network_info()
            self.data_ready.emit(upload, download, adapter_name, connection_type, ssid)
            time.sleep(1)

        self.finished.emit()


class NetworkMonitorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QGridLayout(self)

        # Top Label (Title and Adapter Name)
        top_label = QHBoxLayout()
        self.left_label = QLabel("Network Adapter")
        self.left_label.setStyleSheet("color: white; font-size: 20pt;")
        self.top_right_label = QLabel("Detecting Adapter...")
        self.top_right_label.setStyleSheet("color: white; font-size: 12pt;")
        top_label.addWidget(self.left_label, alignment=Qt.AlignLeft)
        top_label.addWidget(self.top_right_label, alignment=Qt.AlignRight)
        layout.addLayout(top_label, 0, 0, 1, 2)

        # Download Label
        download_label = QHBoxLayout()
        self.download_left_label = QLabel("Download speed")
        self.download_left_label.setStyleSheet("color: white; font-size: 8pt;")
        self.download_right_label = QLabel()
        self.download_right_label.setStyleSheet("color: white; font-size: 8pt;")
        download_label.addWidget(self.download_left_label, alignment=Qt.AlignLeft)
        download_label.addWidget(self.download_right_label, alignment=Qt.AlignRight)
        layout.addLayout(download_label, 1, 0, 1, 2)

        # Download Plot
        self.download_plot = pg.PlotWidget()
        self.download_plot.setBackground('#1C1C1C')
        self.download_plot.getPlotItem().showGrid(x=True, y=True, alpha=0.7)
        self.download_plot.setYRange(0, 1000)
        for axis in ['bottom', 'left', 'top', 'right']:
            self.download_plot.getPlotItem().showAxis(axis, True)
            self.download_plot.getPlotItem().getAxis(axis).setTicks([])
        self.download_plot.getPlotItem().hideButtons()
        self.download_plot.setMouseEnabled(x=False, y=False)
        self.download_curve = self.download_plot.plot(pen=pg.mkPen('m', width=2), fillLevel=0, brush=(255, 0, 255, 80))
        layout.addWidget(self.download_plot, 2, 0, 1, 2)

        x_label_layout = QHBoxLayout()
        self.left_label = QLabel("60 seconds")
        self.left_label.setStyleSheet("color: #E0E0E0; font-size: 8pt;")
        self.right_label = QLabel("0")
        self.right_label.setStyleSheet("color: #E0E0E0; font-size: 8pt;")
        x_label_layout.addWidget(self.left_label, alignment=Qt.AlignLeft)  # Align left
        x_label_layout.addWidget(self.right_label, alignment=Qt.AlignRight) # Align right
        layout.addLayout(x_label_layout, 3, 0, 1, 2)

        # Upload Label
        upload_label = QHBoxLayout()
        self.upload_left_label = QLabel("Upload speed")
        self.upload_left_label.setStyleSheet("color: white; font-size: 8pt;")
        self.upload_right_label = QLabel()
        self.upload_right_label.setStyleSheet("color: white; font-size: 8pt;")
        upload_label.addWidget(self.upload_left_label, alignment=Qt.AlignLeft)
        upload_label.addWidget(self.upload_right_label, alignment=Qt.AlignRight)
        layout.addLayout(upload_label, 4, 0, 1, 2)

        # Upload Plot
        self.upload_plot = pg.PlotWidget()
        self.upload_plot.setBackground('#1C1C1C')
        self.upload_plot.getPlotItem().showGrid(x=True, y=True, alpha=0.7)
        self.upload_plot.setYRange(0, 1000)
        for axis in ['bottom', 'left', 'top', 'right']:
            self.upload_plot.getPlotItem().showAxis(axis, True)
            self.upload_plot.getPlotItem().getAxis(axis).setTicks([])
        self.upload_plot.getPlotItem().hideButtons()
        self.upload_plot.setMouseEnabled(x=False, y=False)
        self.upload_curve = self.upload_plot.plot(pen=pg.mkPen('g', width=2), fillLevel=0, brush=(0, 255, 0, 80))
        layout.addWidget(self.upload_plot, 5, 0, 1, 2)

        x_label_layout = QHBoxLayout()
        self.left_label = QLabel("60 seconds")
        self.left_label.setStyleSheet("color: #E0E0E0; font-size: 8pt;")
        self.right_label = QLabel("0")
        self.right_label.setStyleSheet("color: #E0E0E0; font-size: 8pt;")
        x_label_layout.addWidget(self.left_label, alignment=Qt.AlignLeft)  # Align left
        x_label_layout.addWidget(self.right_label, alignment=Qt.AlignRight) # Align right
        layout.addLayout(x_label_layout, 6, 0, 1, 2)

        # Detail label
        self.details_label = QLabel()
        self.details_label.setStyleSheet("color: #E0E0E0; font-size: 9pt;")
        self.details_label.setWordWrap(True)
        layout.addWidget(self.details_label, 7, 0, 1, 2)

        layout.setRowStretch(0, 0)
        layout.setRowStretch(1, 0)
        layout.setRowStretch(2, 8)
        layout.setRowStretch(3, 0)
        layout.setRowStretch(4, 0)
        layout.setRowStretch(5, 4)
        layout.setRowStretch(6, 0)
        layout.setRowStretch(7, 0)

        # Initialize data
        self.upload_data = [0] * 60
        self.download_data = [0] * 60

        # Worker thread setup
        self.thread = QThread()
        self.worker = NetworkWorker()
        self.worker.moveToThread(self.thread)
        self.worker.data_ready.connect(self.update_display)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def update_display(self, upload, download, adapter_name, connection_type, ssid):
        self.upload_data = self.upload_data[1:] + [upload]
        self.download_data = self.download_data[1:] + [download]

        self.upload_curve.setData(self.upload_data)
        self.download_curve.setData(self.download_data)

        def format_speed(speed_kbps):
            if speed_kbps < 1000:
                return f"{int(speed_kbps)} Kbps"
            elif speed_kbps < 1024 * 1000:
                return f"{int(speed_kbps / 1024)} Mbps"
            else:
                return f"{speed_kbps / (1024 * 8):.2f} MB/s"

        upload_label = format_speed(upload)
        download_label = format_speed(download)

        self.upload_right_label.setText(upload_label)
        self.download_right_label.setText(download_label)
        self.top_right_label.setText(adapter_name)

        self.details_label.setText(
            f"<b>Upload:</b> {upload_label}<br>"
            f"<b>Download:</b> {download_label}<br>"
            f"<b>Type:</b> {connection_type}<br>"
            f"<b>SSID:</b> {ssid}"
        )

    def closeEvent(self, event):
        self.worker.running = False
        self.thread.quit()
        self.thread.wait()
        self.worker.deleteLater()
        super().closeEvent(event)
