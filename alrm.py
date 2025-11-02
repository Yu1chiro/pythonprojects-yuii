import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import json
import os
from pathlib import Path
import threading
import time
from pygame import mixer

class SchoolAlarmManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Alarm Management 2025")
        self.root.state('zoomed')
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Data alarm disimpan di file JSON
        self.data_file = "alarm_data.json"
        self.alarms = self.load_alarms()
        self.is_monitoring = False
        self.triggered_today = set()  # Track alarm yang sudah berbunyi hari ini
        self.current_volume = 1.0  # Volume default (0.0 - 1.0)
        
        # Initialize pygame mixer untuk audio
        mixer.init()
        mixer.music.set_volume(self.current_volume)
        
        self.setup_styles()
        self.setup_ui()
        
        # Mulai monitoring alarm
        self.start_monitoring()
        
    def setup_styles(self):
        self.style.configure("TFrame", background="#f5f5f5")
        self.style.configure("Main.TFrame", background="#f5f5f5")
        self.style.configure("Card.TFrame", background="white")
        self.style.configure("Header.TFrame", background="#2196F3")
        self.style.configure("Header.TLabel", 
                             background="#2196F3", 
                             foreground="white", 
                             font=("Segoe UI", 24, "bold"))
        self.style.configure("TLabel", background="white", font=("Segoe UI", 12))
        self.style.configure("Main.TLabel", background="#f5f5f5", font=("Segoe UI", 12))
        self.style.configure("Time.TLabel", font=("Segoe UI", 32, "bold"), foreground="#181818", background="white")
        self.style.configure("Status.TLabel", font=("Segoe UI", 12), foreground="#666", background="white")
        self.style.configure("Playing.TLabel", font=("Segoe UI", 14, "bold"), foreground="#0DC913", background="white")
        self.style.configure("Volume.TLabel", font=("Segoe UI", 12, "bold"), foreground="#151617", background="white")
        self.style.configure("TButton", font=("Segoe UI", 12, "bold"), padding=(20, 10), cursor="hand2")
        self.style.configure("Success.TButton", background="#4CAF50", foreground="white")
        self.style.map("Success.TButton", background=[('active', '#45a049'), ('disabled', '#ccc')])
        self.style.configure("Primary.TButton", background="#2196F3", foreground="white")
        self.style.map("Primary.TButton", background=[('active', '#1976D2'), ('disabled', '#ccc')])
        self.style.configure("Danger.TButton", background="#f44336", foreground="white")
        self.style.map("Danger.TButton", background=[('active', '#d32f2f'), ('disabled', '#ccc')])
        self.style.configure("Warning.TButton", background="#FF9800", foreground="white")
        self.style.map("Warning.TButton", background=[('active', '#F57C00')])
        self.style.configure("TLabelframe", background="white", relief="solid", borderwidth=1)
        self.style.configure("TLabelframe.Label", background="white", font=("Segoe UI", 12, "bold"), foreground="#333")
        
    def setup_ui(self):
        # Header
        header_frame = ttk.Frame(self.root, style="Header.TFrame", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = ttk.Label(header_frame, text="🔔 ALARM MANAGER | 2025", style="Header.TLabel")
        title_label.pack(pady=15)
        
        # Scrollable canvas
        canvas_container = ttk.Frame(self.root, style="Main.TFrame")
        canvas_container.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(canvas_container, bg="#f5f5f5", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.scrollable_frame = ttk.Frame(self.canvas, style="Main.TFrame")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="n")
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        content_frame = ttk.Frame(self.scrollable_frame, style="Main.TFrame")
        content_frame.pack(padx=40, pady=40)
        
        # Current Time Display
        time_card = ttk.Labelframe(content_frame, text="🕐 JAM SEKARANG")
        time_card.pack(fill="x", pady=(0, 20), ipady=20, ipadx=15)
        
        time_inner = ttk.Frame(time_card, style="Card.TFrame")
        time_inner.pack(fill="x", padx=20, pady=10)
        
        self.current_time_label = ttk.Label(time_inner, text="--:--:--", style="Time.TLabel")
        self.current_time_label.pack()
        
        self.current_date_label = ttk.Label(time_inner, text="", style="Status.TLabel")
        self.current_date_label.pack(pady=(5, 0))
        
        # Status Playing
        self.status_playing_label = ttk.Label(time_inner, text="", style="Playing.TLabel")
        self.status_playing_label.pack(pady=(10, 0))
        
        # Volume Control Section
        volume_card = ttk.Labelframe(content_frame, text="🔊 PENGATURAN VOLUME")
        volume_card.pack(fill="x", pady=(0, 20), ipady=15, ipadx=15)
        
        volume_inner = ttk.Frame(volume_card, style="Card.TFrame", padding=(15, 10))
        volume_inner.pack(fill="x")
        
        volume_control_frame = ttk.Frame(volume_inner, style="Card.TFrame")
        volume_control_frame.pack(fill="x")
        
        ttk.Label(volume_control_frame, text="Volume:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 15))
        
        self.volume_scale = tk.Scale(
            volume_control_frame,
            from_=0,
            to=100,
            orient="horizontal",
            command=self.update_volume,
            length=400,
            font=("Segoe UI", 9),
            bg="white",
            fg="#2196F3",
            troughcolor="#e0e0e0",
            activebackground="#1976D2",
            highlightthickness=0,
            cursor="hand2"
        )
        self.volume_scale.set(int(self.current_volume * 100))
        self.volume_scale.pack(side="left", padx=10, fill="x", expand=True)
        
        self.volume_label = ttk.Label(volume_control_frame, text=f"{int(self.current_volume * 100)}%", 
                                      style="Volume.TLabel", width=6)
        self.volume_label.pack(side="left", padx=(10, 0))
        
        # Add New Alarm Section
        add_card = ttk.Labelframe(content_frame, text="➕ TAMBAH ALARM")
        add_card.pack(fill="x", pady=(0, 20), ipady=15, ipadx=15)
        
        add_inner = ttk.Frame(add_card, style="Card.TFrame", padding=(15, 10))
        add_inner.pack(fill="x")
        
        # Alarm Name
        name_frame = ttk.Frame(add_inner, style="Card.TFrame")
        name_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(name_frame, text="Nama Alarm:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=(0, 10))
        self.alarm_name_entry = ttk.Entry(name_frame, font=("Segoe UI", 12), width=40)
        self.alarm_name_entry.pack(side="left", fill="x", expand=True)
        
        # Time Input
        time_frame = ttk.Frame(add_inner, style="Card.TFrame")
        time_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(time_frame, text="Jam:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=(0, 10))
        
        self.hour_var = tk.StringVar(value="11")
        self.minute_var = tk.StringVar(value="30")
        
        hour_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, width=8, textvariable=self.hour_var, 
                                   font=("Segoe UI", 12, "bold"), justify="center")
        hour_spinbox.pack(side="left", padx=10)
        
        ttk.Label(time_frame, text=":", font=("Segoe UI", 12, "bold")).pack(side="left")
        
        minute_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, width=8, textvariable=self.minute_var,
                                     font=("Segoe UI", 12, "bold"), justify="center")
        minute_spinbox.pack(side="left", padx=10)
        
        ttk.Label(time_frame, text="(Format 24 Jam)", font=("Segoe UI", 10, "italic"), 
                 foreground="#777").pack(side="left", padx=10)
        
        # Audio File
        audio_frame = ttk.Frame(add_inner, style="Card.TFrame")
        audio_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(audio_frame, text="File Audio:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=(0, 10))
        
        self.audio_path_label = ttk.Label(audio_frame, text="Belum ada file dipilih", 
                                          font=("Segoe UI", 9), foreground="#999")
        self.audio_path_label.pack(side="left", fill="x", expand=True)
        
        audio_btn = ttk.Button(audio_frame, text="📂 Pilih Audio", command=self.select_audio, 
                              style="Primary.TButton")
        audio_btn.pack(side="right", padx=(10, 0))
        
        self.selected_audio = None
        
        # Add Button
        add_btn_frame = ttk.Frame(add_inner, style="Card.TFrame")
        add_btn_frame.pack(fill="x", pady=(10, 0))
        
        add_alarm_btn = ttk.Button(add_btn_frame, text="➕ TAMBAH ALARM", 
                                   command=self.add_alarm, style="Success.TButton")
        add_alarm_btn.pack()
        
        # Alarm List Section
        list_card = ttk.Labelframe(content_frame, text="📋 DAFTAR ALARM AKTIF")
        list_card.pack(fill="both", expand=True, ipady=15, ipadx=15)
        
        list_inner = ttk.Frame(list_card, style="Card.TFrame", padding=(15, 10))
        list_inner.pack(fill="both", expand=True)
        self.style.configure("Treeview", 
                     font=("Segoe UI", 11),  # Font untuk isi tabel
                     rowheight=30)  # Tinggi baris agar pas dengan font besar

        self.style.configure("Treeview.Heading", 
                     font=("Segoe UI", 12, "bold"))
        # Treeview untuk daftar alarm
        columns = ("Nama", "Jam", "Audio")
        self.alarm_tree = ttk.Treeview(list_inner, columns=columns, show="headings", height=10)
        
        self.alarm_tree.heading("Nama", text="Nama Alarm")
        self.alarm_tree.heading("Jam", text="Jam")
        self.alarm_tree.heading("Audio", text="File Audio")
        
        self.alarm_tree.column("Nama", width=250, anchor="center")
        self.alarm_tree.column("Jam", width=120, anchor="center")
        self.alarm_tree.column("Audio", width=400, anchor="center")
        
        self.alarm_tree.pack(fill="both", expand=True, pady=(0, 10))
        
        # Action Buttons
        action_frame = ttk.Frame(list_inner, style="Card.TFrame")
        action_frame.pack(fill="x")
        
        test_btn = ttk.Button(action_frame, text="🔊 Test Audio", 
                             command=self.test_alarm, style="Primary.TButton")
        test_btn.pack(side="left", padx=(0, 10))
        
        stop_btn = ttk.Button(action_frame, text="⏹️ Stop Audio", 
                             command=self.stop_audio, style="Warning.TButton")
        stop_btn.pack(side="left", padx=(0, 10))
        
        delete_btn = ttk.Button(action_frame, text="🗑️ Hapus Alarm", 
                               command=self.delete_alarm, style="Danger.TButton")
        delete_btn.pack(side="left")
        
        # Footer
        footer = ttk.Label(content_frame, text="© AM SMANTIARA | PBJ 22", 
                          font=("Segoe UI", 9), foreground="#999", background="#f5f5f5")
        footer.pack(pady=20)
        
        # Load existing alarms
        self.refresh_alarm_list()
        
    def update_volume(self, value):
        """Update volume saat slider digerakkan"""
        volume = int(float(value))
        self.current_volume = volume / 100
        mixer.music.set_volume(self.current_volume)
        self.volume_label.config(text=f"{volume}%")
        
    def select_audio(self):
        filename = filedialog.askopenfilename(
            title="Pilih File Audio",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.ogg"),
                ("MP3", "*.mp3"),
                ("WAV", "*.wav"),
                ("OGG", "*.ogg"),
                ("All Files", "*.*")
            ]
        )
        
        if filename:
            self.selected_audio = filename
            audio_name = os.path.basename(filename)
            self.audio_path_label.config(text=f"🎵 {audio_name}", foreground="#4CAF50")
            
    def add_alarm(self):
        name = self.alarm_name_entry.get().strip()
        hour = self.hour_var.get().zfill(2)
        minute = self.minute_var.get().zfill(2)
        
        if not name:
            messagebox.showwarning("Peringatan", "Nama alarm tidak boleh kosong!")
            return
            
        if not self.selected_audio:
            messagebox.showwarning("Peringatan", "Pilih file audio terlebih dahulu!")
            return
            
        # Validasi waktu
        try:
            time_str = f"{hour}:{minute}"
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            messagebox.showerror("Error", "Format waktu tidak valid!")
            return
            
        # Cek duplikat waktu
        for alarm in self.alarms:
            if alarm["time"] == time_str:
                messagebox.showwarning("Peringatan", 
                                      f"Sudah ada alarm di jam {time_str}!\nEdit atau hapus alarm tersebut terlebih dahulu.")
                return
        
        # Tambahkan alarm
        alarm_data = {
            "name": name,
            "time": time_str,
            "audio": self.selected_audio
        }
        
        self.alarms.append(alarm_data)
        self.save_alarms()
        self.refresh_alarm_list()
        
        # Reset form
        self.alarm_name_entry.delete(0, tk.END)
        self.hour_var.set("08")
        self.minute_var.set("00")
        self.selected_audio = None
        self.audio_path_label.config(text="Belum ada file dipilih", foreground="#999")
        
        messagebox.showinfo("Sukses", f"Alarm '{name}' berhasil ditambahkan!")
        
    def delete_alarm(self):
        selection = self.alarm_tree.selection()
        if not selection:
            messagebox.showwarning("Peringatan", "Pilih alarm yang ingin dihapus!")
            return
            
        item = self.alarm_tree.item(selection[0])
        alarm_name = item["values"][0]
        alarm_time = item["values"][1]
        
        confirm = messagebox.askyesno("Konfirmasi", 
                                      f"Hapus alarm '{alarm_name}' (Jam {alarm_time})?")
        if confirm:
            # Hapus dari list
            self.alarms = [a for a in self.alarms if not (a["name"] == alarm_name and a["time"] == alarm_time)]
            self.save_alarms()
            self.refresh_alarm_list()
            messagebox.showinfo("Sukses", "Alarm berhasil dihapus!")
            
    def test_alarm(self):
        selection = self.alarm_tree.selection()
        if not selection:
            messagebox.showwarning("Peringatan", "Pilih alarm yang ingin di-test!")
            return
            
        item = self.alarm_tree.item(selection[0])
        alarm_name = item["values"][0]
        alarm_time = item["values"][1]
        
        # Cari alarm
        alarm = next((a for a in self.alarms if a["name"] == alarm_name and a["time"] == alarm_time), None)
        if alarm:
            self.play_audio(alarm["audio"], alarm["name"])
            
    def stop_audio(self):
        try:
            mixer.music.stop()
            self.status_playing_label.config(text="")
            print("Audio dihentikan")
        except:
            pass
            
    def refresh_alarm_list(self):
        # Hapus semua item
        for item in self.alarm_tree.get_children():
            self.alarm_tree.delete(item)
            
        # Tambahkan alarm (sort berdasarkan waktu)
        for alarm in sorted(self.alarms, key=lambda x: x["time"]):
            audio_name = os.path.basename(alarm["audio"])
            
            self.alarm_tree.insert("", tk.END, values=(
                alarm["name"],
                alarm["time"],
                audio_name
            ))
            
    def start_monitoring(self):
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_alarms, daemon=True)
        self.monitor_thread.start()
        
        # Update current time display
        self.update_current_time()
        
        # Reset triggered_today setiap hari baru
        self.reset_daily_trigger()
        
    def update_current_time(self):
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%A, %d %B %Y")
        
        self.current_time_label.config(text=time_str)
        self.current_date_label.config(text=date_str)
        
        # Update setiap detik
        self.root.after(1000, self.update_current_time)
        
    def reset_daily_trigger(self):
        """Reset triggered alarms setiap tengah malam"""
        now = datetime.now()
        # Cek apakah sudah lewat tengah malam
        if now.hour == 0 and now.minute == 0:
            self.triggered_today.clear()
            print("🔄 Reset alarm harian")
        
        # Cek lagi setiap 1 menit
        self.root.after(60000, self.reset_daily_trigger)
        
    def monitor_alarms(self):
        """Monitor alarm tanpa modal popup"""
        last_checked_minute = None
        
        while self.is_monitoring:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            current_date = now.strftime("%Y-%m-%d")
            
            # Hanya cek ketika menit berganti (hindari multiple trigger)
            if current_time != last_checked_minute:
                last_checked_minute = current_time
                
                # Cek setiap alarm
                for alarm in self.alarms:
                    alarm_key = f"{alarm['time']}_{current_date}"
                    
                    # Trigger alarm jika waktu cocok dan belum triggered hari ini
                    if alarm["time"] == current_time and alarm_key not in self.triggered_today:
                        self.triggered_today.add(alarm_key)
                        self.trigger_alarm(alarm)
            
            time.sleep(1)  # Cek setiap detik
            
    def trigger_alarm(self, alarm):
        """Trigger alarm - langsung play audio tanpa popup"""
        print(f"🔔 ALARM TRIGGERED: {alarm['name']} at {alarm['time']}")
        
        # Play audio
        self.play_audio(alarm["audio"], alarm["name"])
        
    def play_audio(self, audio_path, alarm_name="Test"):
        """Play audio dan otomatis stop setelah selesai"""
        try:
            if not os.path.exists(audio_path):
                print(f"Error: File audio tidak ditemukan - {audio_path}")
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    f"File audio tidak ditemukan:\n{audio_path}"))
                return
            
            # Stop audio yang sedang berjalan
            mixer.music.stop()
            
            # Load dan play audio baru dengan volume yang sudah diset
            mixer.music.load(audio_path)
            mixer.music.set_volume(self.current_volume)
            mixer.music.play()
            
            # Update status
            self.root.after(0, lambda: self.status_playing_label.config(
                text=f"🔊 Memutar: {alarm_name}"
            ))
            
            print(f"🔊 Playing audio: {os.path.basename(audio_path)} (Volume: {int(self.current_volume * 100)}%)")
            
            # Monitor audio sampai selesai, lalu auto-stop
            threading.Thread(target=self.wait_audio_finish, daemon=True).start()
            
        except Exception as e:
            print(f"Error playing audio: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", 
                f"Gagal memutar audio:\n{str(e)}"))
            
    def wait_audio_finish(self):
        """Tunggu audio selesai, lalu auto-clear status"""
        while mixer.music.get_busy():
            time.sleep(0.5)
        
        # Audio sudah selesai
        print("✅ Audio selesai diputar")
        self.root.after(0, lambda: self.status_playing_label.config(text=""))
            
    def load_alarms(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
        
    def save_alarms(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.alarms, f, indent=2, ensure_ascii=False)
            
    def on_closing(self):
        self.is_monitoring = False
        try:
            mixer.music.stop()
            mixer.quit()
        except:
            pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SchoolAlarmManager(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()