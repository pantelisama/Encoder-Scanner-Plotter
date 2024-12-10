import tkinter as tk
from tkinter import ttk, filedialog
import socket
import threading
import time
import re
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class TCPClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TCP Client Terminal")
        self.root.geometry("1200x800")  # Adjusted window size to fit multiple plots

        # TCP connection variables
        self.socket_connection = None
        self.is_running = False
        self.current_pan = ""  # Store the latest pan value
        self.current_tilt = ""  # Store the latest tilt value
        self.current_height = ""  # Store the latest height value
        self.timestamp_data = []  # List to store timestamps
        self.pan_data = []  # List to store pan values
        self.tilt_data = []  # List to store tilt values
        self.height_data = []  # List to store height values

        # Server IP and Port Entry for TCP
        self.ip_label = ttk.Label(root, text="Server IP (TCP):")
        self.ip_label.grid(row=0, column=0, padx=5, pady=5)

        self.ip_entry = ttk.Entry(root, width=30)
        self.ip_entry.insert(0, "192.1.0.41")  # Default IP
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5)

        self.port_label = ttk.Label(root, text="Port (TCP):")
        self.port_label.grid(row=1, column=0, padx=5, pady=5)

        self.port_entry = ttk.Entry(root, width=30)
        self.port_entry.insert(0, "30301")  # Default Port
        self.port_entry.grid(row=1, column=1, padx=5, pady=5)

        # Connection Buttons
        self.connect_tcp_button = ttk.Button(root, text="Connect to TCP", command=self.connect_to_tcp_server)
        self.connect_tcp_button.grid(row=2, column=0, padx=5, pady=5)

        self.disconnect_button = ttk.Button(root, text="Disconnect", command=self.disconnect, state="disabled")
        self.disconnect_button.grid(row=2, column=1, padx=5, pady=5)

        # Client Monitor (TCP Data)
        self.client_monitor_label = ttk.Label(root, text="Client Monitor:")
        self.client_monitor_label.grid(row=3, column=0, padx=5, pady=5)

        self.client_monitor = tk.Text(root, height=10, width=70,
                                      wrap=tk.WORD)  # Client monitor to display received data
        self.client_monitor.grid(row=4, column=0, columnspan=2, padx=5, pady=5)
        self.client_monitor.config(state=tk.DISABLED)

        # Interpolated Pan, Tilt, Height Label and Text Box
        self.interpolated_data_label = ttk.Label(root, text="Interpolated Pan:")
        self.interpolated_data_label.grid(row=5, column=0, padx=5, pady=5)

        self.interpolated_data_text = ttk.Entry(root, width=30)
        self.interpolated_data_text.grid(row=5, column=1, padx=5, pady=5)

        # New Textbox for timestamp, pan, tilt, height
        self.timestamp_data_label = ttk.Label(root, text="Timestamp,Pan,Tilt,Height:")
        self.timestamp_data_label.grid(row=6, column=0, padx=5, pady=5)

        self.timestamp_data_text = tk.Text(root, height=5, width=70)  # New text box for the timestamp and data
        self.timestamp_data_text.grid(row=7, column=0, columnspan=2, padx=5, pady=5)
        self.timestamp_data_text.config(state=tk.DISABLED)

        # Export Button to save the timestamp and data
        self.export_button = ttk.Button(root, text="Export to Text", command=self.export_to_text)
        self.export_button.grid(row=8, column=0, columnspan=2, padx=5, pady=5)

        # Plotting Section (Separate plots for Pan, Tilt, and Height)
        self.plot_frame = ttk.LabelFrame(root, text="Pan, Tilt, and Height Plots", height=400)
        self.plot_frame.grid(row=9, column=0, columnspan=2, padx=5, pady=5)

        # Create separate figures for Pan, Tilt, and Height
        self.fig_pan, self.ax_pan = plt.subplots(figsize=(6, 3))
        self.ax_pan.set_title("Pan Over Time")
        self.ax_pan.set_xlabel("Timestamp")
        self.ax_pan.set_ylabel("Pan Value")

        self.fig_tilt, self.ax_tilt = plt.subplots(figsize=(6, 3))
        self.ax_tilt.set_title("Tilt Over Time")
        self.ax_tilt.set_xlabel("Timestamp")
        self.ax_tilt.set_ylabel("Tilt Value")

        self.fig_height, self.ax_height = plt.subplots(figsize=(6, 3))
        self.ax_height.set_title("Height Over Time")
        self.ax_height.set_xlabel("Timestamp")
        self.ax_height.set_ylabel("Height Value")

        # Create canvases for each plot and pack them
        self.canvas_pan = FigureCanvasTkAgg(self.fig_pan, master=self.plot_frame)
        self.canvas_pan.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas_tilt = FigureCanvasTkAgg(self.fig_tilt, master=self.plot_frame)
        self.canvas_tilt.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas_height = FigureCanvasTkAgg(self.fig_height, master=self.plot_frame)
        self.canvas_height.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Periodic update every 1 second
        self.root.after(1000, self.update_timestamp_data)

    def connect_to_tcp_server(self):
        """ Connect to the TCP server. """
        ip_address = self.ip_entry.get()
        port = int(self.port_entry.get())

        if not ip_address or not port:
            self.client_monitor.config(state=tk.NORMAL)
            self.client_monitor.insert(tk.END, "Error: Invalid IP or Port.\n")
            self.client_monitor.config(state=tk.DISABLED)
            return

        self.socket_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.socket_connection.connect((ip_address, port))
            self.client_monitor.config(state=tk.NORMAL)
            self.client_monitor.insert(tk.END, f"Connected to {ip_address} at port {port}.\n")
            self.client_monitor.config(state=tk.DISABLED)

            self.is_running = True
            self.connect_tcp_button.config(state=tk.DISABLED)
            self.disconnect_button.config(state=tk.NORMAL)

            # Start TCP read thread
            self.read_thread = threading.Thread(target=self.read_from_tcp, daemon=True)
            self.read_thread.start()

            # Send the sequence of commands after TCP connection is established
            self.send_initial_commands()

        except Exception as e:
            self.client_monitor.config(state=tk.NORMAL)
            self.client_monitor.insert(tk.END, f"Error connecting to server: {e}\n")
            self.client_monitor.config(state=tk.DISABLED)

    def disconnect(self):
        """ Disconnect from the TCP server. """
        self.is_running = False
        if self.socket_connection:
            self.socket_connection.close()

        self.connect_tcp_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)

    def send_initial_commands(self):
        """ Send the required sequence of commands once connected. """
        if self.socket_connection:
            # Initial sequence of commands
            commands = ['5', '\r', '\x1b', 'mc', '\x1b', '\r', 'R', '\r', 'M', '\r', 'A', '\r']
            for command in commands:
                self.socket_connection.sendall(command.encode())
                time.sleep(0.5)  # Increased delay to 0.5 seconds between commands

            # Send '6' followed by 'enter', then 'a' followed by 'enter'
            self.socket_connection.sendall('6'.encode())  # Send '6'
            self.socket_connection.sendall('\r'.encode())  # Send 'enter' (carriage return)
            time.sleep(0.5)

            self.socket_connection.sendall('a'.encode())  # Send 'a'
            self.socket_connection.sendall('\r'.encode())  # Send 'enter' (carriage return)
            time.sleep(0.5)

            # Display that the initial commands were sent
            self.client_monitor.config(state=tk.NORMAL)
            self.client_monitor.insert(tk.END, "Initial commands and additional '6' and 'a' with enters sent.\n")
            self.client_monitor.config(state=tk.DISABLED)

    def display_received_data(self, data):
        """ Display received data in the correct monitor. """
        self.client_monitor.config(state=tk.NORMAL)
        self.client_monitor.insert(tk.END, data)
        self.client_monitor.yview(tk.END)  # Scroll to the bottom automatically
        self.client_monitor.config(state=tk.DISABLED)

    def extract_and_display_data(self, data):
        """ Extract Pan (P), Tilt (T), and Height (H) values from the received data and display them. """
        match = re.search(r'P=(\d+).*?T=(\d+).*?H=(\d+)',
                          data)  # Updated regex to look for 'T=' (Tilt), 'H=' (Height), and 'P=' (Pan)
        if match:
            raw_pan = match.group(1)  # Pan value
            raw_tilt = match.group(2)  # Tilt value
            raw_height = match.group(3)  # Height value

            # Update the Pan, Tilt, and Height text boxes
            self.interpolated_data_text.delete(0, tk.END)
            self.interpolated_data_text.insert(tk.END, raw_pan)

            # Store the values for plotting
            self.current_pan = raw_pan
            self.current_tilt = raw_tilt
            self.current_height = raw_height

            # Store the timestamp, Pan, Tilt, and Height for plotting
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.timestamp_data.append(timestamp)
            self.pan_data.append(int(raw_pan))
            self.tilt_data.append(int(raw_tilt))
            self.height_data.append(int(raw_height))

            # Update the plot with new data
            self.update_plot()

            # Display timestamp, Pan, Tilt, and Height in the text box
            self.display_timestamp_and_data(timestamp, raw_pan, raw_tilt, raw_height)

    def display_timestamp_and_data(self, timestamp, pan, tilt, height):
        """ Display timestamp, Pan, Tilt, and Height in the new textbox. """
        self.timestamp_data_text.config(state=tk.NORMAL)
        self.timestamp_data_text.insert(tk.END, f"{timestamp},{pan},{tilt},{height}\n")
        self.timestamp_data_text.yview(tk.END)  # Scroll to the bottom automatically
        self.timestamp_data_text.config(state=tk.DISABLED)

    def update_plot(self):
        """ Update the plot with the latest data. """
        # Update the Pan plot
        self.ax_pan.clear()
        self.ax_pan.plot(self.timestamp_data, self.pan_data, label="Pan", color="g")
        self.ax_pan.set_title("Pan Over Time")
        self.ax_pan.set_xlabel("Timestamp")
        self.ax_pan.set_ylabel("Pan Value")
        self.ax_pan.tick_params(axis="x", rotation=45)
        self.ax_pan.legend()
        self.canvas_pan.draw()

        # Update the Tilt plot
        self.ax_tilt.clear()
        self.ax_tilt.plot(self.timestamp_data, self.tilt_data, label="Tilt", color="b")
        self.ax_tilt.set_title("Tilt Over Time")
        self.ax_tilt.set_xlabel("Timestamp")
        self.ax_tilt.set_ylabel("Tilt Value")
        self.ax_tilt.tick_params(axis="x", rotation=45)
        self.ax_tilt.legend()
        self.canvas_tilt.draw()

        # Update the Height plot
        self.ax_height.clear()
        self.ax_height.plot(self.timestamp_data, self.height_data, label="Height", color="r")
        self.ax_height.set_title("Height Over Time")
        self.ax_height.set_xlabel("Timestamp")
        self.ax_height.set_ylabel("Height Value")
        self.ax_height.tick_params(axis="x", rotation=45)
        self.ax_height.legend()
        self.canvas_height.draw()
#########################################################################################################################################   start here
    def export_to_text(self):
        """ Export the timestamp and data to a text file. """
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, 'w') as file:
                for i in range(len(self.timestamp_data)):
                    file.write(
                        f"{self.timestamp_data[i]},{self.pan_data[i]},{self.tilt_data[i]},{self.height_data[i]}\n")
###########################################################################################################################################   stop here
    def read_from_tcp(self):
        """ Read data from the TCP server. """
        while self.is_running:
            try:
                data = self.socket_connection.recv(1024).decode("utf-8")
                if data:
                    self.display_received_data(data)
                    self.extract_and_display_data(data)
            except Exception as e:
                print(f"Error receiving data: {e}")
                break

    def update_timestamp_data(self):
        """ Periodically update the timestamp data every second. """
        if self.is_running:
            self.root.after(1000, self.update_timestamp_data)

    def on_closing(self):
        """ Handle the window close event. """
        self.disconnect()
        self.root.quit()


# Create and start the Tkinter application
if __name__ == "__main__":
    root = tk.Tk()
    app = TCPClientApp(root)
    root.mainloop()
