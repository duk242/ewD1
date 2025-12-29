import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import json
import threading
import time
import os
from datetime import datetime
from collections import deque

# --- Constants ---
UDP_PORT = 45
BUFFER_SIZE = 4096
MAX_XID = 999
POLL_INTERVAL = 10  # Seconds (Keep-alive interval)
CONFIG_FILE = "config.txt"

# Graph Settings
GRAPH_HISTORY_SECONDS = 60
GRAPH_UPDATE_MS = 200 # Update graph every 200ms (5fps)
GRAPH_POINTS = int((1000 / GRAPH_UPDATE_MS) * GRAPH_HISTORY_SECONDS)

# --- Global State ---
xid_counter = 0
xid_lock = threading.Lock()

def get_next_xid():
    global xid_counter
    with xid_lock:
        xid_counter += 1
        if xid_counter > MAX_XID:
            xid_counter = 1
        return xid_counter

# --- Networking Class ---
class EWD1Communicator:
    def __init__(self, log_callback, data_callback):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(1.0)
        self.running = True
        self.log_callback = log_callback
        self.data_callback = data_callback
        
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()

    def send_command(self, ip, payload_dict):
        try:
            xid = get_next_xid()
            if "osc" not in payload_dict:
                full_packet = {"osc": {"xid": xid}}
                full_packet.update(payload_dict)
            else:
                full_packet = payload_dict
                if "xid" not in full_packet["osc"]:
                    full_packet["osc"]["xid"] = xid

            message_str = json.dumps(full_packet)
            self.sock.sendto(message_str.encode('utf-8'), (ip, UDP_PORT))
            self.log_callback(ip, message_str, "sent")
        except Exception as e:
            self.log_callback(ip, f"Error sending: {e}", "error")

    def _listen_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(BUFFER_SIZE)
                ip = addr[0]
                message = data.decode('utf-8').strip('\x00')
                self.log_callback(ip, message, "recv")
                try:
                    json_data = json.loads(message)
                    self.data_callback(ip, json_data)
                except json.JSONDecodeError as e:
                    self.log_callback(ip, f"JSON Error: {e}", "error")
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception as e:
                print(f"Listener Error: {e}")

    def close(self):
        self.running = False
        self.sock.close()

# --- GUI Components ---

class AudioGraph(tk.Canvas):
    def __init__(self, master, width=300, height=100, bg="black"):
        super().__init__(master, width=width, height=height, bg=bg)
        self.width = width
        self.height = height
        self.data = deque([-80]*GRAPH_POINTS, maxlen=GRAPH_POINTS)
        
    def add_value(self, db_value):
        if db_value is None: db_value = -80
        if db_value < -80: db_value = -80
        if db_value > 0: db_value = 0
        
        normalized = (db_value + 80) / 80 
        y_pos = self.height - (normalized * self.height)
        self.data.append(y_pos)
        self.draw_graph()

    def draw_graph(self):
        self.delete("all")
        points = []
        step_x = self.width / (GRAPH_POINTS - 1)
        for i, y_val in enumerate(self.data):
            x = i * step_x
            points.extend([x, y_val])
        if len(points) >= 4:
            self.create_line(points, fill="#00ff00", width=1)

class ReceiverBlock(tk.LabelFrame):
    def __init__(self, master, ip):
        super().__init__(master, text=f"Connecting to {ip}...", font=("Arial", 10, "bold"), padx=10, pady=10)
        self.ip = ip
        self.last_seen = 0
        self.current_audio_db = -80
        
        self.default_fg = self.cget("foreground")
        
        self.columnconfigure(1, weight=1)
        
        # Name
        tk.Label(self, text="Name:").grid(row=0, column=0, sticky="e")
        self.lbl_name = tk.Label(self, text="Unknown", font=("Arial", 12, "bold"))
        self.lbl_name.grid(row=0, column=1, sticky="w")
        
        # RF Strength
        tk.Label(self, text="RF Signal:").grid(row=1, column=0, sticky="e")
        self.progress_rf = ttk.Progressbar(self, length=200, mode='determinate', maximum=100)
        self.progress_rf.grid(row=1, column=1, sticky="ew", padx=5)
        self.lbl_rf_val = tk.Label(self, text="0%")
        self.lbl_rf_val.grid(row=1, column=2)
        
        # Battery
        tk.Label(self, text="Battery:").grid(row=2, column=0, sticky="e")
        self.progress_bat = ttk.Progressbar(self, length=200, mode='determinate', maximum=100)
        self.progress_bat.grid(row=2, column=1, sticky="ew", padx=5)
        self.lbl_bat_val = tk.Label(self, text="0%")
        self.lbl_bat_val.grid(row=2, column=2)
        
        # Audio Graph
        tk.Label(self, text="Audio (60s):").grid(row=3, column=0, sticky="ne")
        self.graph = AudioGraph(self, width=250, height=60)
        self.graph.grid(row=3, column=1, columnspan=2, pady=5)
        
        self.update_graph_timer()

    def update_graph_timer(self):
        self.graph.add_value(self.current_audio_db)
        self.after(GRAPH_UPDATE_MS, self.update_graph_timer)

    def update_status(self, name=None, rf=None, bat=None, audio_db=None):
        self.last_seen = time.time()
        
        self.config(fg=self.default_fg, text=f"Receiver: {self.ip}")
        self.lbl_rf_val.config(fg=self.default_fg)
        self.lbl_bat_val.config(fg=self.default_fg)
        
        if name:
            self.lbl_name.config(text=name)
            
        if rf is not None:
            self.progress_rf['value'] = rf
            self.lbl_rf_val.config(text=f"{rf}%")
            color = self.default_fg
            if rf > 70: color = "#00cc00"
            elif rf > 50: color = "#cccc00"
            elif rf > 0: color = "orange"
            self.lbl_rf_val.config(fg=color)

        if bat is not None:
            self.progress_bat['value'] = bat
            self.lbl_bat_val.config(text=f"{bat}%")
            color = self.default_fg
            if bat > 70: color = "#00cc00"
            elif bat > 50: color = "#cccc00"
            elif bat > 0: color = "orange"
            self.lbl_bat_val.config(fg=color)
            
        if audio_db is not None:
            self.current_audio_db = audio_db

    def mark_offline(self):
        self.config(text=f"DISCONNECTED ({self.ip})", fg="red")
        self.lbl_rf_val.config(fg="red", text="OFF")
        self.lbl_bat_val.config(fg="red", text="OFF")
        self.current_audio_db = -80

# --- Main Application ---
class MicMonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sennheiser ewD1 Monitor V6")
        self.geometry("950x850")
        
        self.ips = []
        self.receivers_ui = {}
        self.communicator = EWD1Communicator(self.log_debug, self.handle_packet)
        self.autoscroll = True
        self.polling_active = True
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        
        self.tab_main = ttk.Frame(self.notebook)
        self.tab_settings = ttk.Frame(self.notebook)
        self.tab_debug = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_main, text="Monitor")
        self.notebook.add(self.tab_settings, text="Settings")
        self.notebook.add(self.tab_debug, text="Debug")
        
        self._init_settings_tab()
        self._init_main_tab()
        self._init_debug_tab()
        
        # Load config on startup
        self.load_config()
        
        self.after(2000, self.poller)

    def _init_settings_tab(self):
        frame = ttk.Frame(self.tab_settings, padding=20)
        frame.pack(fill="both")
        tk.Label(frame, text="Microphone IP Addresses (One per line)", font=("Arial", 12)).pack(anchor="w")
        self.txt_ips = scrolledtext.ScrolledText(frame, width=40, height=15)
        self.txt_ips.pack(pady=10, anchor="w")
        tk.Label(frame, text="Click 'Save & Connect' to initialize connections and save config.").pack(anchor="w")
        btn_save = ttk.Button(frame, text="Save & Connect", command=self.save_settings)
        btn_save.pack(anchor="w", pady=5)

    def _init_main_tab(self):
        # Top Control Bar
        ctrl_frame = ttk.Frame(self.tab_main, padding=5)
        ctrl_frame.pack(fill="x", side="top")
        
        self.btn_poll_toggle = tk.Button(ctrl_frame, text="Polling: ON", bg="#ccffcc", command=self.toggle_polling, font=("Arial", 10, "bold"), width=15)
        self.btn_poll_toggle.pack(side="left")
        
        tk.Label(ctrl_frame, text=" (Controls automatic messages)").pack(side="left")

        # Scrollable Area
        self.canvas_main = tk.Canvas(self.tab_main)
        self.scrollbar = ttk.Scrollbar(self.tab_main, orient="vertical", command=self.canvas_main.yview)
        self.scrollable_frame = ttk.Frame(self.canvas_main)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas_main.configure(scrollregion=self.canvas_main.bbox("all")))
        self.canvas_main.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas_main.configure(yscrollcommand=self.scrollbar.set)
        self.canvas_main.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def _init_debug_tab(self):
        frame = ttk.Frame(self.tab_debug)
        frame.pack(fill="both", expand=True)
        
        ctrl_frame = ttk.Frame(frame)
        ctrl_frame.pack(fill="x", padx=5, pady=5)
        self.btn_autoscroll = tk.Button(ctrl_frame, text="Auto-Scroll: ON", bg="#ccffcc", command=self.resume_autoscroll)
        self.btn_autoscroll.pack(side="right")
        
        self.txt_debug = scrolledtext.ScrolledText(frame, state='disabled', bg="black", fg="white", font=("Consolas", 9))
        self.txt_debug.pack(fill="both", expand=True, padx=5, pady=5)
        self.txt_debug.tag_config("sent", foreground="yellow")
        self.txt_debug.tag_config("recv", foreground="#00ff00")
        self.txt_debug.tag_config("error", foreground="red")
        
        cmd_frame = ttk.Frame(frame)
        cmd_frame.pack(fill="x", padx=5, pady=5)
        tk.Label(cmd_frame, text="Send Raw JSON:").pack(side="left")
        self.entry_raw = tk.Entry(cmd_frame)
        self.entry_raw.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_raw.insert(0, '{"device":{"name":null}}')
        self.combo_ip_debug = ttk.Combobox(cmd_frame, values=self.ips, width=15)
        self.combo_ip_debug.pack(side="left")
        btn_send = ttk.Button(cmd_frame, text="Send", command=self.send_raw)
        btn_send.pack(side="left", padx=5)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    content = f.read()
                    self.txt_ips.insert("1.0", content)
                    # Automatically populate internal list, but don't connect yet until user clicks Save 
                    # (or we could, but better to let user verify first)
                    self.ips = [line.strip() for line in content.split('\n') if line.strip()]
                    self.combo_ip_debug['values'] = self.ips
                    if self.ips: self.combo_ip_debug.current(0)
            except Exception as e:
                messagebox.showerror("Config Error", f"Failed to load config: {e}")

    def save_config(self, ip_text):
        try:
            with open(CONFIG_FILE, "w") as f:
                f.write(ip_text)
        except Exception as e:
            messagebox.showerror("Config Error", f"Failed to save config: {e}")

    def toggle_polling(self):
        self.polling_active = not self.polling_active
        if self.polling_active:
            self.btn_poll_toggle.config(text="Polling: ON", bg="#ccffcc")
        else:
            self.btn_poll_toggle.config(text="Polling: PAUSED", bg="#ffcccc")

    def resume_autoscroll(self):
        self.autoscroll = True
        self.btn_autoscroll.config(text="Auto-Scroll: ON", bg="#ccffcc")
        self.txt_debug.see(tk.END)

    def save_settings(self):
        content = self.txt_ips.get("1.0", tk.END).strip()
        self.save_config(content)
        
        new_ips = [line.strip() for line in content.split('\n') if line.strip()]
        self.ips = new_ips[:10]
        self.combo_ip_debug['values'] = self.ips
        if self.ips: self.combo_ip_debug.current(0)
        
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.receivers_ui.clear()
        
        # Reset polling to Active when saving/restarting
        self.polling_active = True
        self.btn_poll_toggle.config(text="Polling: ON", bg="#ccffcc")

        for ip in self.ips:
            block = ReceiverBlock(self.scrollable_frame, ip)
            block.pack(fill="x", pady=5, padx=10)
            self.receivers_ui[ip] = block
            self.send_subscription(ip)
            self.communicator.send_command(ip, {"device": {"name": None}})
        
        if not self.ips:
            messagebox.showinfo("Settings", "No IPs configured.")
        else:
            messagebox.showinfo("Settings", f"Configured {len(self.ips)} receivers.")

    def send_subscription(self, ip):
        sub_payload = { "osc": { "state": { "subscribe": [{ "rx1": {"rf_quality": None, "warnings": None}, "mates": {"tx1": {"warnings": None, "bat_gauge": None}}, "audio": {"out1": {"level_db": None}} }] } } }
        self.communicator.send_command(ip, sub_payload)

    def poller(self):
        # Only run network logic if polling is active
        if self.polling_active:
            for ip in self.ips:
                self.send_subscription(ip)
                if ip in self.receivers_ui:
                    block = self.receivers_ui[ip]
                    # Only mark offline if we are actively polling. 
                    # If paused, we assume silence is intentional.
                    if time.time() - block.last_seen > 15 and block.last_seen != 0:
                        block.mark_offline()
        
        # Always reschedule the timer, even if paused
        self.after(POLL_INTERVAL * 1000, self.poller)

    def send_raw(self):
        ip = self.combo_ip_debug.get()
        raw_str = self.entry_raw.get()
        if not ip: return
        try:
            payload = json.loads(raw_str)
            self.communicator.send_command(ip, payload)
        except json.JSONDecodeError:
            self.log_debug("System", "Invalid JSON format", "error")

    def log_debug(self, ip, message, tag):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{ip}] {message}\n"
        self.after(0, lambda: self._append_log(formatted, tag))

    def _append_log(self, text, tag):
        is_at_bottom = self.txt_debug.yview()[1] == 1.0
        if not is_at_bottom:
            self.autoscroll = False
            self.btn_autoscroll.config(text="Resume Autoscroll", bg="#ffcccc")
        self.txt_debug.config(state='normal')
        self.txt_debug.insert(tk.END, text, tag)
        if self.autoscroll:
            self.txt_debug.see(tk.END)
        self.txt_debug.config(state='disabled')

    def handle_packet(self, ip, data):
        self.after(0, lambda: self._process_data(ip, data))

    def _process_data(self, ip, data):
        if ip not in self.receivers_ui: return
        block = self.receivers_ui[ip]
        name, rf, bat, level = None, None, None, None
        
        def get_nested(d, path_keys):
            current = d
            for k in path_keys:
                if isinstance(current, dict) and k in current: current = current[k]
                elif isinstance(current, list): return None
                else: return None
            return current

        val = get_nested(data, ["audio", "out1", "level_db"])
        if val is None:
            subs = get_nested(data, ["osc", "state", "subscribe"])
            if subs and isinstance(subs, list) and len(subs) > 0: val = get_nested(subs[0], ["audio", "out1", "level_db"])
        if val is not None: level = float(val)

        val = get_nested(data, ["device", "name"])
        if val is not None: name = str(val)

        val = get_nested(data, ["rx1", "rf_quality"])
        if val is None:
            subs = get_nested(data, ["osc", "state", "subscribe"])
            if subs and isinstance(subs, list) and len(subs) > 0: val = get_nested(subs[0], ["rx1", "rf_quality"])
        if val is not None: rf = int(val)

        val = get_nested(data, ["mates", "tx1", "bat_gauge"])
        if val is None:
            subs = get_nested(data, ["osc", "state", "subscribe"])
            if subs and isinstance(subs, list) and len(subs) > 0: val = get_nested(subs[0], ["mates", "tx1", "bat_gauge"])
        if val is not None: bat = int(val)

        if any(x is not None for x in [name, rf, bat, level]):
            block.update_status(name, rf, bat, level)

if __name__ == "__main__":
    app = MicMonitorApp()
    app.protocol("WM_DELETE_WINDOW", lambda: (app.communicator.close(), app.destroy()))
    app.mainloop()
