import psutil
import time
import wmi
from datetime import timedelta
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer, Qt
from pyqtgraph import TextItem
import pyqtgraph as pg


class CPUWorker(QObject):
    data_updated = pyqtSignal(float, dict)

    def __init__(self, interval=1000):
        super().__init__()
        self.interval = interval
        self.timer = None
        try:
            # c = wmi.WMI()
            self.cpu_name = wmi.WMI().Win32_Processor()[0].Name
        except:
            self.cpu_name = "Unknown CPU"

        try:
            self.l1_cache, self.l2_cache, self.l2_cache = 0, 0, 0
            for cache in wmi.WMI().Win32_CacheMemory():
                if(cache.Level == 3):
                    self.l1_cache += cache.InstalledSize
                elif(cache.Level == 4):
                    self.l2_cache += cache.InstalledSize
                elif(cache.Level == 5):
                    self.l3_cache += cache.InstalledSize
        except:
            self.l1_cache = None
            self.l2_cache = None
            self.l3_cache = None

    def start_timer(self):
        # This will run in the worker thread context
        self.timer = QTimer(self)
        self.timer.setInterval(self.interval)
        self.timer.timeout.connect(self.collect_data)
        self.timer.start()

    def collect_data(self):
        usage = psutil.cpu_percent(interval=None)
        cpu_freq = psutil.cpu_freq()
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_td = timedelta(seconds=int(uptime_seconds))
        days = uptime_td.days
        hours, remainder = divmod(uptime_td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}:{hours}:{minutes}:{seconds}"

        process_count = len(list(psutil.process_iter(['pid'])))
        thread_count = 0
        for p in psutil.process_iter(['pid']):
            try:
                if p.is_running():
                    thread_count += p.num_threads()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        cpu_info = {
            "name": self.cpu_name,
            "utilization": usage,
            "freq": cpu_freq,
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "processes": process_count,
            "threads": thread_count,
            "uptime": uptime_str,
            "L1_cache": self.l1_cache,
            "L2_cache": self.l2_cache,
            "L3_cache": self.l3_cache
        }
        self.data_updated.emit(usage, cpu_info)

    def stop(self):
        self.running = False
        if self.timer:
            self.timer.stop()
            self.timer.deleteLater()


class CPUMonitorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.cpu_usage_data = [0] * 60

        self.worker = CPUWorker(interval=1000)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.start_timer)
        self.worker.data_updated.connect(self.update_ui)
        self.worker_thread.start()

        layout = QGridLayout(self)

        top_label = QHBoxLayout()
        self.left_label = QLabel("CPU")
        self.left_label.setStyleSheet("color: white; font-size: 20pt;")
        self.right_label = QLabel(self.worker.cpu_name)
        self.right_label.setStyleSheet("color: white; font-size: 12pt;")
        top_label.addWidget(self.left_label, alignment=Qt.AlignLeft)
        top_label.addWidget(self.right_label, alignment=Qt.AlignRight)
        layout.addLayout(top_label, 0, 0, 1, 2)

        # Add labels as QLabel on top of the plot
        top_labels_layout = QHBoxLayout()
        self.top_left_label = QLabel("% Utilization")
        self.top_left_label.setStyleSheet("color: white; font-size: 8pt;")
        self.top_right_label = QLabel("100%")
        self.top_right_label.setStyleSheet("color: white; font-size: 8pt;")
        top_labels_layout.addWidget(self.top_left_label, alignment=Qt.AlignLeft)
        top_labels_layout.addWidget(self.top_right_label, alignment=Qt.AlignRight)
        layout.addLayout(top_labels_layout, 1, 0, 1, 2)

        self.cpu_plot = pg.PlotWidget()
        self.cpu_plot.setBackground('#1C1C1C')
        self.cpu_plot.getPlotItem().showGrid(x=True, y=True, alpha=0.7)
        self.cpu_plot.getPlotItem().showAxis('top',True)
        self.cpu_plot.getPlotItem().showAxis('right',True)
        self.cpu_plot.getPlotItem().getAxis('bottom').setTicks([])
        self.cpu_plot.getPlotItem().getAxis('left').setTicks([])
        self.cpu_plot.getPlotItem().getAxis('top').setTicks([])
        self.cpu_plot.getPlotItem().getAxis('right').setTicks([])
        self.cpu_plot.setYRange(0, 100)
        self.cpu_plot.setMouseEnabled(x=False, y=False)
        self.cpu_plot.setMenuEnabled(False)
        self.cpu_plot.getPlotItem().hideButtons()
        self.cpu_curve = self.cpu_plot.plot(pen=pg.mkPen('#00BFFF',width=2), fillLevel=0, brush=(0,191,255,80))
        self.cpu_plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cpu_plot.setMinimumHeight(300)
        self.cpu_plot.setMinimumWidth(600)
        layout.addWidget(self.cpu_plot, 2, 0, 1, 2)
        
        x_label_layout = QHBoxLayout()
        self.left_label = QLabel("60 seconds")
        self.left_label.setStyleSheet("color: #E0E0E0; font-size: 8pt;")
        self.right_label = QLabel("0")
        self.right_label.setStyleSheet("color: #E0E0E0; font-size: 8pt;")
        x_label_layout.addWidget(self.left_label, alignment=Qt.AlignLeft)  # Align left
        x_label_layout.addWidget(self.right_label, alignment=Qt.AlignRight) # Align right
        layout.addLayout(x_label_layout, 3, 0, 1, 2)

        self.details_label = QLabel()
        self.details_label.setStyleSheet("color: #E0E0E0; font-size: 9pt;")
        self.details_label.setWordWrap(True)
        layout.addWidget(self.details_label, 4, 0, 1, 2)

        layout.setRowStretch(0, 0)   # top labels row small
        layout.setRowStretch(1, 0)  # plot row large
        layout.setRowStretch(2, 10)   # bottom labels small
        layout.setRowStretch(3, 0)   # details label small
        layout.setRowStretch(4, 0)

    def update_ui(self, usage, cpu_info):
        self.cpu_usage_data = self.cpu_usage_data[1:] + [usage]
        x_values = list(range(len(self.cpu_usage_data)))
        self.cpu_curve.setData(self.cpu_usage_data)
        # f"<b>Processor:</b> {cpu_info['name']}<br>"
        freq = cpu_info["freq"]
        details = (
            f"<b>Utilization:</b> {cpu_info['utilization']}<br>"
            f"<b>CPU Frequency:</b> {freq.current:.2f} MHz (Min: {freq.min}, Max: {freq.max})<br>"
            f"<b>Cores:</b> Physical: {cpu_info['physical_cores']}, Logical: {cpu_info['logical_cores']}<br>"
            f"<b>Processes:</b> {cpu_info['processes']}<br>"
            f"<b>Threads:</b> {cpu_info['threads']}<br>"
            f"<b>Uptime:</b> {cpu_info['uptime']}<br>"
        )
        if cpu_info["L1_cache"]:
            details += (
                f"<b>L1 Cache:</b> {cpu_info['l1_cache']}<br>"
                f"<b>L2 Cache:</b> {cpu_info['l2_cache']}<br>"
                f"<b>L3 Cache:</b> {cpu_info['l3_cache']}<br>"
            )
        else:
            details += "<i>Install py-cpuinfo for cache info.</i>"

        self.details_label.setText(details)

    def closeEvent(self, event):
        self.worker.stop()
        self.worker_thread.quit()
        self.worker_thread.wait()
        self.worker.deleteLater()
        event.accept()

