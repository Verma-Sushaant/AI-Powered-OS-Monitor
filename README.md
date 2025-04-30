# AI-Powered OS Monitor

## Overview
The AI-Powered OS Monitor is a real-time system monitoring application that provides insights into CPU, memory, disk, network, and GPU usage. It features machine learning-based anomaly detection and predictive analytics to alert users about potential system issues. The application includes an interactive GUI for visualizing system performance.

## Features
- **Real-Time Monitoring:** Tracks CPU, memory, disk, network, and GPU usage.
- **Predictive Analytics:** Forecasts resource usage trends.
- **Interactive Visualization:** Displays real-time system metrics with dynamic graphs.
- **Custom Alerts:** Notifies users when resource usage exceeds defined thresholds.

## Project Structure
```
AI-Powered-OS-Monitor/
|── system_monitor/
|   |── __init__.py
|   │── cpu_details.py        # Fetches and analyzes CPU usage data
|   │── memory_details.py     # Monitors memory usage
|   │── disk_details.py       # Tracks disk usage statistics
|
|── hardwre-monitor/
|   |── __init__.py
|   │── network_details.py    # Monitors network activity
|   │── gpu_details.py        # Retrieves GPU performance metrics
|
|── application/
|   |── __init__.py
|   │── main.py               # Integrates all modules and runs the GUI
|
│── README.md             # Project documentation
```

## Installation
### Prerequisites
- Python 3.x

### Steps to Run the Application
1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/AI-Powered-OS-Monitor.git
   ```
2. Navigate to the project directory:
   ```sh
   cd AI-Powered-OS-Monitor
   ```
3. Run the application:
   ```sh
   python main.py
   ```

## Usage
- The application launches a GUI displaying real-time graphs and system performance metrics.
- Alerts pop up if an anomaly is detected.
- Users can check historical trends for system resource usage.

## Future Enhancements
- Extend monitoring for multiple devices.
- Add remote monitoring and mobile integration.
- Implement cloud-based system performance tracking.
- Will use AI models to detect abnormal system behavior.

## License
This project is licensed under Creative Commons (CC BY-NC 4.0).

## Author
- [Sushaant Verma] - [Verma-Sushaant](https://github.com/Verma-Sushaant)
- [Aditya Sharma] - [Aditya0988](https://github.com/Aditya0988)
- [Vivek] - [vivekk2005](https://github.com/vivekk2005)

## Contributions
Contributions are welcome! Please create a pull request or raise an issue if you'd like to improve the project.
