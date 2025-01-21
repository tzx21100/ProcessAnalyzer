A simple program used to check CPU performance of processes.
Mainly to be used for Games and put data into csv files.

Go to src > dist to find the .exe

How It Works

Process Retrieval:

Uses psutil to fetch a list of running processes.

Retrieves accurate CPU usage by calling psutil.cpu_percent twice, with a short interval between calls.

Background Threads:

CPU usage and process information are fetched in a separate thread to avoid blocking the GUI.

Data is communicated to the main thread using a thread-safe queue.

Real-Time Graphing:

matplotlib is used to plot CPU and memory usage dynamically.

CSV Export:

Each monitored process has its performance metrics saved to a separate CSV file for later analysis.