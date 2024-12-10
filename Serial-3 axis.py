import tkinter as tk
from tkinter import ttk, filedialog
import serial
import threading
import time
import re
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from collections import deque

class SerialMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial Monitor")
        self.root.geometry("800x600")

        # Serial connection variables
        self.serial_connection = None
        self.is_running = False

        # Plot configuration
        self.pan_data = deque([0] * 100, maxlen=100)  # Store the last 100 pan values
        self.tilt_data = deque([0] * 100, maxlen=100)  # Store the last 100 tilt values
        self.height_data = deque([0] * 100, maxlen=100)  # Store the last 100 height values
        self.plot_update_interval = 100  # Update interval for the plot in milliseconds

        # UI Elements
        self.connect_button = ttk.Button(root, text="Connect", command=self.connect_serial)
        self.connect_button.grid(row=0, column=0, padx=5, pady=5)

        self.disconnect_button = ttk.Button(root, text="Disconnect", command=self.disconnect_serial, state=tk.DISABLED)
        self.disconnect_button.grid(row=0, column=1, padx=5, pady=5)

        self.command_entry = ttk.Entry(root, width=50)
        self.command_entry.grid(row=1, column=0, padx=5, pady=5)
        self.command_entry.bind("<Return>", self.send_command)

        self.serial_monitor_label = ttk.Label(root, text="Serial Monitor:")
        self.serial_monitor_label.grid(row=2, column=0, padx=5, pady=5)

        self.serial_monitor = tk.Text(root, height=10, width=70, wrap=tk.WORD)
        self.serial_monitor.grid(row=3, column=0, columnspan=2, padx=5, pady=5)
        self.serial_monitor.config(state=tk.DISABLED)

        # PAN, TILT, HEIGHT value textboxes
        self.pan_label = ttk.Label(root, text="PAN:")
        self.pan_label.grid(row=4, column=0, padx=5, pady=5)
        self.pan_value_text = ttk.Entry(root, width=30)
        self.pan_value_text.grid(row=4, column=1, padx=5, pady=5)

        self.tilt_label = ttk.Label(root, text="TILT:")
        self.tilt_label.grid(row=5, column=0, padx=5, pady=5)
        self.tilt_value_text = ttk.Entry(root, width=30)
        self.tilt_value_text.grid(row=5, column=1, padx=5, pady=5)

        self.height_label = ttk.Label(root, text="HEIGHT:")
        self.height_label.grid(row=6, column=0, padx=5, pady=5)
        self.height_value_text = ttk.Entry(root, width=30)
        self.height_value_text.grid(row=6, column=1, padx=5, pady=5)

        self.timestamp_label = ttk.Label(root, text="Timestamp & Values:")
        self.timestamp_label.grid(row=7, column=0, padx=5, pady=5)

        self.timestamp_textbox = tk.Text(root, height=5, width=70)
        self.timestamp_textbox.grid(row=8, column=0, columnspan=2, padx=5, pady=5)
        self.timestamp_textbox.config(state=tk.DISABLED)

        self.export_button = ttk.Button(root, text="Export to TXT", command=self.export_to_txt)
        self.export_button.grid(row=9, column=0, columnspan=2, pady=5)

        # Add plot frames
        self.plot_frame_pan = ttk.LabelFrame(root, text="Real-Time PAN Plot")
        self.plot_frame_pan.grid(row=10, column=0, padx=5, pady=10, sticky="nsew")

        self.plot_frame_tilt = ttk.LabelFrame(root, text="Real-Time TILT Plot")
        self.plot_frame_tilt.grid(row=11, column=0, padx=5, pady=10, sticky="nsew")

        self.plot_frame_height = ttk.LabelFrame(root, text="Real-Time HEIGHT Plot")
        self.plot_frame_height.grid(row=12, column=0, padx=5, pady=10, sticky="nsew")

        # Create plots for PAN, TILT, and HEIGHT
        self.fig_pan, self.ax_pan = plt.subplots(figsize=(5, 3))
        self.ax_pan.set_title("PAN Over Time")
        self.ax_pan.set_xlabel("Time (Last 100 Points)")
        self.ax_pan.set_ylabel("PAN Values")
        self.pan_line, = self.ax_pan.plot([], [], color="red", linewidth=2, label="PAN")
        self.ax_pan.legend()

        self.fig_tilt, self.ax_tilt = plt.subplots(figsize=(5, 3))
        self.ax_tilt.set_title("TILT Over Time")
        self.ax_tilt.set_xlabel("Time (Last 100 Points)")
        self.ax_tilt.set_ylabel("TILT Values")
        self.tilt_line, = self.ax_tilt.plot([], [], color="green", linewidth=2, label="TILT")
        self.ax_tilt.legend()

        self.fig_height, self.ax_height = plt.subplots(figsize=(5, 3))
        self.ax_height.set_title("HEIGHT Over Time")
        self.ax_height.set_xlabel("Time (Last 100 Points)")
        self.ax_height.set_ylabel("HEIGHT Values")
        self.height_line, = self.ax_height.plot([], [], color="blue", linewidth=2, label="HEIGHT")
        self.ax_height.legend()

        # Embed the plots in Tkinter
        self.canvas_pan = FigureCanvasTkAgg(self.fig_pan, self.plot_frame_pan)
        self.canvas_widget_pan = self.canvas_pan.get_tk_widget()
        self.canvas_widget_pan.pack(fill=tk.BOTH, expand=True)

        self.canvas_tilt = FigureCanvasTkAgg(self.fig_tilt, self.plot_frame_tilt)
        self.canvas_widget_tilt = self.canvas_tilt.get_tk_widget()
        self.canvas_widget_tilt.pack(fill=tk.BOTH, expand=True)

        self.canvas_height = FigureCanvasTkAgg(self.fig_height, self.plot_frame_height)
        self.canvas_widget_height = self.canvas_height.get_tk_widget()
        self.canvas_widget_height.pack(fill=tk.BOTH, expand=True)

        # Start plot update loop
        self.update_plots()

    def update_plots(self):
        """ Update the real-time plots with new data. """
        # Update the data for the three plots: PAN, TILT, and HEIGHT
        self.pan_line.set_data(range(len(self.pan_data)), list(self.pan_data))
        self.tilt_line.set_data(range(len(self.tilt_data)), list(self.tilt_data))
        self.height_line.set_data(range(len(self.height_data)), list(self.height_data))

        # Dynamically adjust x and y axis limits
        self.ax_pan.set_xlim(0, len(self.pan_data))
        self.ax_tilt.set_xlim(0, len(self.tilt_data))
        self.ax_height.set_xlim(0, len(self.height_data))

        # Adjust y-limits dynamically based on the data range
        if len(self.pan_data) > 1:
            self.ax_pan.set_ylim(min(self.pan_data) - 10, max(self.pan_data) + 10)
        if len(self.tilt_data) > 1:
            self.ax_tilt.set_ylim(min(self.tilt_data) - 10, max(self.tilt_data) + 10)
        if len(self.height_data) > 1:
            self.ax_height.set_ylim(min(self.height_data) - 10, max(self.height_data) + 10)

        # Redraw each canvas
        self.canvas_pan.draw()
        self.canvas_tilt.draw()
        self.canvas_height.draw()

        # Update plots every 'plot_update_interval' milliseconds
        self.root.after(self.plot_update_interval, self.update_plots)

    def connect_serial(self):
        """ Establish a serial connection. """
        try:
            # COM7, 115200 baud rate, Odd parity
            self.serial_connection = serial.Serial('COM7', 115200, parity=serial.PARITY_ODD, timeout=1)
            if self.serial_connection.is_open:
                self.is_running = True
                self.connect_button.config(state=tk.DISABLED)
                self.disconnect_button.config(state=tk.NORMAL)
                self.serial_monitor.config(state=tk.NORMAL)
                self.serial_monitor.insert(tk.END, "Connected to COM7 at 115200 baud with Odd parity.\n")
                self.serial_monitor.config(state=tk.DISABLED)

                # Start reading from the serial port
                self.read_thread = threading.Thread(target=self.read_from_serial, daemon=True)
                self.read_thread.start()

                self.send_initial_commands()
                self.send_r_thread = threading.Thread(target=self.send_r_periodically, daemon=True)
                self.send_r_thread.start()

        except Exception as e:
            self.serial_monitor.config(state=tk.NORMAL)
            self.serial_monitor.insert(tk.END, f"Error connecting to serial port: {e}\n")
            self.serial_monitor.config(state=tk.DISABLED)

    def read_from_serial(self):
        """ Read data from the serial port and display it in the monitor. """
        while self.is_running:
            try:
                data = self.serial_connection.readline().decode('utf-8').strip()
                if data:
                    self.display_received_data(data)
                    self.extract_values_from_data(data)
            except Exception as e:
                if self.is_running:
                    self.serial_monitor.config(state=tk.NORMAL)
                    self.serial_monitor.insert(tk.END, f"Error reading serial data: {e}\n")
                    self.serial_monitor.config(state=tk.DISABLED)
                break

    def display_received_data(self, data):
        """ Display the received serial data in the monitor. """
        self.serial_monitor.config(state=tk.NORMAL)
        self.serial_monitor.insert(tk.END, f"Received: {data}\n")
        self.serial_monitor.yview(tk.END)
        self.serial_monitor.config(state=tk.DISABLED)

    def send_command(self, event=None):
        """ Send the command entered in the command box to the serial port. """
        command = self.command_entry.get().strip()
        if command and self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.write(command.encode() + b'\r')
            self.serial_monitor.config(state=tk.NORMAL)
            self.serial_monitor.insert(tk.END, f"Sent: {command}\n")
            self.serial_monitor.config(state=tk.DISABLED)
            self.command_entry.delete(0, tk.END)

    def send_initial_commands(self):
        """ Send the initial set of commands (M, 8, 3, R). """
        if self.serial_connection and self.serial_connection.is_open:
            initial_commands = ['M', '8', '3', 'R']
            for command in initial_commands:
                self.serial_connection.write(command.encode() + b'\r')
                time.sleep(1)
                self.serial_monitor.config(state=tk.NORMAL)
                self.serial_monitor.insert(tk.END, f"Sent: {command}\n")
                self.serial_monitor.config(state=tk.DISABLED)

    def send_r_periodically(self):
        """ Continuously send R every 1 second. """
        while self.is_running:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.write(b'R\r')
                time.sleep(1)

    def disconnect_serial(self):
        """ Disconnect the serial connection. """
        if self.serial_connection and self.serial_connection.is_open:
            self.is_running = False
            self.serial_connection.close()
            self.connect_button.config(state=tk.NORMAL)
            self.disconnect_button.config(state=tk.DISABLED)
            self.serial_monitor.config(state=tk.NORMAL)
            self.serial_monitor.insert(tk.END, "Disconnected from serial port.\n")
            self.serial_monitor.config(state=tk.DISABLED)

    def extract_values_from_data(self, data):
        """ Extract PAN, TILT, HEIGHT values and update them in the textboxes. """
        pan_value = None
        tilt_value = None
        height_value = None

        # Use regex to extract PAN, TILT, HEIGHT values from data
        pan_match = re.search(r"PAN:\s*(\d+)", data)
        tilt_match = re.search(r"TILT:\s*(\d+)", data)
        height_match = re.search(r"HEIGHT:\s*(\d+)", data)

        if pan_match:
            pan_value = int(pan_match.group(1))
            self.pan_value_text.delete(0, tk.END)
            self.pan_value_text.insert(tk.END, str(pan_value))
            self.pan_data.append(pan_value)

        if tilt_match:
            tilt_value = int(tilt_match.group(1))
            self.tilt_value_text.delete(0, tk.END)
            self.tilt_value_text.insert(tk.END, str(tilt_value))
            self.tilt_data.append(tilt_value)

        if height_match:
            height_value = int(height_match.group(1))
            self.height_value_text.delete(0, tk.END)
            self.height_value_text.insert(tk.END, str(height_value))
            self.height_data.append(height_value)

        # Log timestamped data in the textbox
        if pan_value is not None and tilt_value is not None and height_value is not None:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            # Use root.after to safely update the timestamp textbox
            self.root.after(self.update_timestamp_textbox, timestamp, pan_value, tilt_value, height_value)

    def update_timestamp_textbox(self, timestamp, pan_value, tilt_value, height_value):
        """ Update the timestamp textbox with the new data. """
        self.timestamp_textbox.config(state=tk.NORMAL)
        self.timestamp_textbox.insert(tk.END, f"{timestamp}, {pan_value}, {tilt_value}, {height_value}\n")
        self.timestamp_textbox.yview(tk.END)
        self.timestamp_textbox.config(state=tk.DISABLED)

    def export_to_txt(self):
        """ Export logged timestamped data to a text file. """
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write(self.timestamp_textbox.get(1.0, tk.END))
            self.serial_monitor.config(state=tk.NORMAL)
            self.serial_monitor.insert(tk.END, f"Data exported to {file_path}\n")
            self.serial_monitor.config(state=tk.DISABLED)

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = SerialMonitorApp(root)
    root.mainloop()
