import tkinter as tk
from tkinter import messagebox
import psutil
import time
from threading import Thread
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import csv
import os
# Global variables to hold process data
processes_to_watch = {}  # Dictionary to store PID and process name
cpu_usage = {}
memory_usage = {}
timestamps = {}

#saving CS files
TARGET_DIR = "./monitoring_results"  # Change this to your desired path
os.makedirs(TARGET_DIR, exist_ok=True)  # Ensure the directory exists

# Function to get a list of running processes
def get_process_list():
    filtered_processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'username','cpu_percent']):
            try:
                # Get process information
                pid = proc.info['pid']
                name = proc.info['name']
                username = proc.info['username']
                cpu = proc.info['cpu_percent']
                
                # Exclude system processes (adjust based on your OS)
                if username in ["SYSTEM", "Local Service", "Network Service"]:
                    continue
                
                # Exclude known system/idle processes
                if name.lower() in ["system idle process", "system", "svchost.exe", "csrss.exe"]:
                    continue
                
                # Add the process to the list if it passes all filters
                filtered_processes.append((pid, name))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception as e:
        messagebox.showerror("Error", f"Error fetching processes: {e}")
    
    return filtered_processes
    
# Monitor the selected process

def monitor_process(pid):
    try:
        process = psutil.Process(pid)
        app_name = processes_to_watch[pid]
        global cpu_usage, memory_usage, timestamps

        # Initialize CPU usage measurement
        process.cpu_percent(interval=None)  # First call initializes metrics

        # Open CSV file for writing
         # Set the file path
        filename = os.path.join(TARGET_DIR, f"{app_name}_monitoring.csv")

        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Write the header
            writer.writerow(["Time (s)", "CPU Usage (%)", "Memory Usage (MB)"])

            start_time = time.time()
            while pid in processes_to_watch:
                # Collect CPU and memory usage
                cpu = process.cpu_percent(interval=1)  # Short interval for meaningful data
                memory = process.memory_info().rss / 1024 / 1024  # Convert memory to MB
                elapsed_time = time.time() - start_time

                # Debug: Log the collected metrics
                #print(f"PID: {pid}, CPU: {cpu:.2f}, Memory: {memory:.2f} MB, Time: {elapsed_time:.2f}")

                # Safely append data to dictionaries
                if pid in cpu_usage and pid in memory_usage and pid in timestamps:
                    cpu_usage[pid].append(cpu)
                    memory_usage[pid].append(memory)
                    timestamps[pid].append(elapsed_time)

                    # Write row to CSV
                    writer.writerow([elapsed_time, cpu, memory])
                else:
                    break  # Stop monitoring if the process is no longer tracked
    except psutil.NoSuchProcess:
        messagebox.showinfo("Info", f"Monitoring stopped: Process {pid} ended.")
    except Exception as e:
        print(f"Error monitoring process {pid}: {e}")

# Start monitoring in a separate thread
def start_monitoring(pid):
    if pid not in cpu_usage:
        cpu_usage[pid] = []  # Initialize with an empty list
    if pid not in memory_usage:
        memory_usage[pid] = []  # Initialize with an empty list
    if pid not in timestamps:
        timestamps[pid] = []  # Initialize with an empty list

    thread = Thread(target=monitor_process, args=(pid,), daemon=True)
    thread.start()

# Update the graph in real-time
def update_graph(frame, ax):
    ax.clear()
    for pid in list(processes_to_watch):  # Iterate over monitored processes
        if pid in timestamps and timestamps[pid]:  # Check for valid data
            app_name = processes_to_watch[pid]  # Get the application's name
            current_cpu = cpu_usage[pid][-1] if cpu_usage[pid] else 0  # Get the latest CPU usage
            current_memory = memory_usage[pid][-1] if memory_usage[pid] else 0  # Get the latest memory usage

            # Debugging output
            #print(f"Updating graph for PID {pid}: CPU={current_cpu}%, Memory={current_memory}MB")

            # Plot CPU and memory usage over time
            ax.plot(timestamps[pid], cpu_usage[pid], label=f"{app_name} - CPU (%)")
            ax.plot(timestamps[pid], memory_usage[pid], label=f"{app_name} - Memory (MB)")

            # Add dynamic text annotations for CPU and Memory
            ax.text(timestamps[pid][-1], cpu_usage[pid][-1], f"{current_cpu:.1f}%", fontsize=8)
            ax.text(timestamps[pid][-1], memory_usage[pid][-1], f"{current_memory:.1f} MB", fontsize=8)

    # Graph aesthetics
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Usage")
    ax.set_title("Process Performance Over Time")
    ax.legend(loc='upper left')


# Function to handle process selection
def select_process():
    try:
        selected = process_listbox.get(process_listbox.curselection())
        pid = int(selected.split(" ")[0])
        if pid not in processes_to_watch:
            processes_to_watch[pid] = selected.split(" - ")[1]
            messagebox.showinfo("Info", f"Monitoring process: {selected}")
            start_monitoring(pid)
            update_watched_processes()
        else:
            messagebox.showwarning("Warning", f"Process {pid} is already being monitored.")
    except tk.TclError:
        messagebox.showerror("Error", "Please select a process to monitor.")

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

    # Function to handle cleanup on close
    def on_close():
        # Stop monitoring processes
        processes_to_watch.clear()
        cpu_usage.clear()
        memory_usage.clear()
        timestamps.clear()

        # Print a message for confirmation (optional)
        print("Monitoring stopped. Exiting application.")
        
        # Destroy the Tkinter window
        root.destroy()

    # Bind the cleanup function to the close event
    root.protocol("WM_DELETE_WINDOW", on_close)

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
