import tkinter as tk
from tkinter import messagebox
import psutil
import time
from threading import Thread
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation

# Global variables to hold process data
processes_to_watch = {}  # Dictionary to store PID and process name
cpu_usage = {}
memory_usage = {}
timestamps = {}

# Function to get a list of running processes
def get_process_list():
    return [(proc.pid, proc.name()) for proc in psutil.process_iter(['pid', 'name'])]

# Monitor the selected process
def monitor_process(pid):
    try:
        process = psutil.Process(pid)
        global cpu_usage, memory_usage, timestamps
        cpu_usage[pid] = []
        memory_usage[pid] = []
        timestamps[pid] = []

        start_time = time.time()
        while pid in processes_to_watch:
            cpu = process.cpu_percent(interval=1)
            memory = process.memory_info().rss / 1024 / 1024  # Convert to MB
            elapsed_time = time.time() - start_time

            cpu_usage[pid].append(cpu)
            memory_usage[pid].append(memory)
            timestamps[pid].append(elapsed_time)

    except psutil.NoSuchProcess:
        messagebox.showinfo("Info", f"Monitoring stopped: Process {pid} ended.")

# Start monitoring in a separate thread
def start_monitoring(pid):
    thread = Thread(target=monitor_process, args=(pid,), daemon=True)
    thread.start()

# Update the graph in real-time
def update_graph(frame, ax):
    ax.clear()
    for pid in list(processes_to_watch):  # Iterate over a copy of keys
        if pid in timestamps and timestamps[pid]:  # Check if pid exists and has data
            ax.plot(timestamps[pid], cpu_usage[pid], label=f"CPU [PID {pid}] (%)")
            ax.plot(timestamps[pid], memory_usage[pid], label=f"Memory [PID {pid}] (MB)")
        else:
            # Skip missing or invalid data
            print(f"Skipping PID {pid} (no data or process ended)")
            if pid in processes_to_watch:
                del processes_to_watch[pid]  # Clean up if the process ended
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Usage")
    ax.set_title("Process Performance")
    ax.legend()
    ax.tight_layout()

# Function to handle process selection
def select_process():
    selected = process_listbox.get(process_listbox.curselection())
    pid = int(selected.split(" ")[0])
    if pid not in processes_to_watch:
        processes_to_watch[pid] = selected.split(" - ")[1]
        messagebox.showinfo("Info", f"Monitoring process: {selected}")
        start_monitoring(pid)
        update_watched_processes()
    else:
        messagebox.showwarning("Warning", f"Process {pid} is already being monitored.")

# Update the list of watched processes
def update_watched_processes():
    watched_listbox.delete(0, tk.END)
    for pid, name in processes_to_watch.items():
        watched_listbox.insert(tk.END, f"{pid} - {name}")

# Terminate a monitored process
def terminate_process():
    try:
        selected = watched_listbox.get(watched_listbox.curselection())
        pid = int(selected.split(" ")[0])
        if pid in processes_to_watch:
            del processes_to_watch[pid]
            cpu_usage.pop(pid, None)
            memory_usage.pop(pid, None)
            timestamps.pop(pid, None)
            update_watched_processes()
            messagebox.showinfo("Info", f"Stopped monitoring process {pid}.")
        else:
            messagebox.showerror("Error", f"Process {pid} is not being monitored.")
    except Exception as e:
        messagebox.showerror("Error", "Please select a process to terminate.")

# Create the GUI
def create_gui():
    global process_listbox, watched_listbox

    # Initialize the main window
    root = tk.Tk()
    root.title("Process Analyzer")

    # Create a frame for the process selection
    frame_left = tk.Frame(root)
    frame_left.pack(side=tk.LEFT, padx=10, pady=10)

    # Add a label
    tk.Label(frame_left, text="Select a running process to monitor:").pack(pady=5)

    # Add a listbox to display processes
    process_listbox = tk.Listbox(frame_left, width=50, height=15)
    process_listbox.pack(pady=5)

    # Populate the listbox with running processes
    for pid, name in get_process_list():
        process_listbox.insert(tk.END, f"{pid} - {name}")

    # Add a button to start monitoring
    tk.Button(frame_left, text="Start Monitoring", command=select_process).pack(pady=5)

    # Add a label for monitored processes
    tk.Label(frame_left, text="Currently Monitored Processes:").pack(pady=5)

    # Add a listbox to display monitored processes
    watched_listbox = tk.Listbox(frame_left, width=50, height=10)
    watched_listbox.pack(pady=5)

    # Add a terminate button
    tk.Button(frame_left, text="Stop Monitoring", command=terminate_process).pack(pady=5)

    # Create a frame for the graph
    frame_right = tk.Frame(root)
    frame_right.pack(side=tk.RIGHT, padx=10, pady=10)

    # Add the graph using matplotlib
    fig, ax = plt.subplots()
    canvas = FigureCanvasTkAgg(fig, master=frame_right)
    canvas.get_tk_widget().pack()

    # Start the real-time graphing
    ani = FuncAnimation(fig, update_graph, fargs=(ax,), interval=1000)

    # Start the Tkinter event loop
    root.mainloop()

# Main function
if __name__ == "__main__":
    create_gui()
