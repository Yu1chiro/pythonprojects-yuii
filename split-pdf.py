import customtkinter as ctk
from tkinter import filedialog
from tkinter import messagebox
from pypdf import PdfReader, PdfWriter
import os


def proses_ekstraksi():
    global file_path_global
    
    if not file_path_global:
        messagebox.showerror("Error", "Silakan pilih file PDF terlebih dahulu.")
        return

    start_str = entry_start.get()
    end_str = entry_end.get()

    try:
        halaman_awal = int(start_str)
        halaman_akhir = int(end_str)

        if halaman_awal <= 0 or halaman_akhir <= 0:
            raise ValueError("Nomor halaman harus positif.")
        if halaman_awal > halaman_akhir:
            raise ValueError("Halaman awal tidak boleh lebih besar dari halaman akhir.")
            
    except ValueError:
        messagebox.showerror("Error", "Input halaman tidak valid. Harap masukkan angka yang benar (cth: 10).")
        return

    nama_dasar, ekstensi = os.path.splitext(os.path.basename(file_path_global))
    nama_file_baru_disarankan = f"{nama_dasar}_halaman_{halaman_awal}-{halaman_akhir}{ekstensi}"

    save_path = filedialog.asksaveasfilename(
        title="Simpan PDF Baru Sebagai...",
        initialfile=nama_file_baru_disarankan,
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")]
    )

    if not save_path:
        return

    # 3. Proses Ekstraksi PDF
    try:
        reader = PdfReader(file_path_global)
        writer = PdfWriter()
        
        total_halaman_asli = len(reader.pages)
        if halaman_awal > total_halaman_asli:
            messagebox.showerror("Error", f"Halaman awal ({halaman_awal}) melebihi total halaman file ({total_halaman_asli}).")
            return

        start_index = halaman_awal - 1
        end_index = halaman_akhir 

        halaman_ditambahkan = 0
        for i in range(start_index, end_index):
            if i < total_halaman_asli:
                writer.add_page(reader.pages[i])
                halaman_ditambahkan += 1
            else:
                break
        
        if halaman_ditambahkan == 0:
            messagebox.showwarning("Warning", "Tidak ada halaman yang diekstrak. Periksa rentang halaman Anda.")
            return

        with open(save_path, 'wb') as output_pdf:
            writer.write(output_pdf)

        messagebox.showinfo("Sukses!", f"Berhasil mengekstrak {halaman_ditambahkan} halaman.\n\nFile baru disimpan di:\n{save_path}")

    except Exception as e:
        messagebox.showerror("Error", f"Terjadi kesalahan tak terduga:\n{e}")


def pilih_file():
    """Membuka dialog untuk memilih file PDF"""
    global file_path_global
    
    filepath = filedialog.askopenfilename(
        title="Pilih File PDF",
        filetypes=[("PDF files", "*.pdf")]
    )
    
    if filepath:
        file_path_global = filepath
        nama_file = os.path.basename(filepath)
        label_file.configure(text=nama_file)
    else:
        file_path_global = ""
        label_file.configure(text="Belum ada file dipilih")

# --- Pengaturan GUI ---

file_path_global = ""
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("PDF Organized by Hera")
app.geometry("450x350")

frame = ctk.CTkFrame(master=app)
frame.pack(pady=20, padx=20, fill="both", expand=True)

button_pilih = ctk.CTkButton(master=frame, text="Upload File PDF", command=pilih_file, height=40)
button_pilih.pack(pady=15)

label_file = ctk.CTkLabel(master=frame, text="Belum ada file dipilih", font=("Arial", 12))
label_file.pack(pady=5)

entry_frame = ctk.CTkFrame(master=frame, fg_color="transparent")
entry_frame.pack(pady=10)

label_start = ctk.CTkLabel(master=entry_frame, text="Halaman Awal:")
label_start.pack(side="left", padx=5)
entry_start = ctk.CTkEntry(master=entry_frame, width=60, placeholder_text="Cth: 10")
entry_start.pack(side="left", padx=5)

label_end = ctk.CTkLabel(master=entry_frame, text="Halaman Akhir:")
label_end.pack(side="left", padx=5)
entry_end = ctk.CTkEntry(master=entry_frame, width=60, placeholder_text="Cth: 15")
entry_end.pack(side="left", padx=5)

button_ekstrak = ctk.CTkButton(
    master=frame, 
    text="Convert (Ekstrak & Simpan)", 
    command=proses_ekstraksi,
    height=50,
    font=("Arial", 14, "bold")
)
button_ekstrak.pack(pady=20, fill="x", padx=30)

deskripsi_teks = (
    "Cara Penggunaan:\n"
    "1. Klik 'Upload File PDF' untuk memilih file.\n"
    "2. Masukkan rentang halaman yang ingin diekstrak (Contoh: Awal 15, Akhir 20).\n"
    "3. Klik 'Convert' untuk memproses dan menyimpan file"
)

label_instruksi = ctk.CTkLabel(
    master=frame, 
    text=deskripsi_teks,
    font=("Arial", 15),
    justify="left"
)
label_instruksi.pack(pady=(0, 10), padx=30, fill="x")



if __name__ == "__main__":
    
    try:
        import pyi_splash
        pyi_splash.close()
    except ImportError:
        pass
    
    app.mainloop()