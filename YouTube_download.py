from tkinter import *
from tkinter import ttk, filedialog, messagebox
from threading import Thread
from pytubefix import YouTube, Playlist
from pytubefix.exceptions import RegexMatchError
import urllib.parse as up
import time, re, os, requests, webbrowser
from io import BytesIO
from PIL import Image, ImageTk

# ---------- Tk Setup ----------
root = Tk()
root.title("🎥 YouTube Downloader")
root.geometry("850x700+200+50")
root.configure(bg="#1e1e1e")

# ---------- Scrollable Frame ----------
main_canvas = Canvas(root, bg="#1e1e1e", highlightthickness=0)
scrollbar = Scrollbar(root, orient=VERTICAL, command=main_canvas.yview)
scrollable_frame = Frame(main_canvas, bg="#1e1e1e")

scrollable_frame.bind(
    "<Configure>",
    lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
)

main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
main_canvas.configure(yscrollcommand=scrollbar.set)

main_canvas.pack(side=LEFT, fill=BOTH, expand=True)
scrollbar.pack(side=RIGHT, fill=Y)

# ---------- Functions ----------
def sanitize_title(title):
    return re.sub(r'[\\/*?:"<>|]', "", title)

def normalize_youtube_url(url):
    parsed = up.urlparse(url)
    if "youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc:
        return url
    raise RegexMatchError("Invalid YouTube URL")

def update_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percent = (bytes_downloaded / total_size) * 100
    elapsed_time = time.time() - start_time

    try:
        speed = bytes_downloaded / elapsed_time
        remaining_time = (bytes_remaining / speed) if speed > 0 else 0
        speed_kbps = speed / 1024
    except ZeroDivisionError:
        speed_kbps, remaining_time = 0, 0

    progress_var.set(percent)
    progress_label.config(
        text=f"{percent:.2f}% | {speed_kbps:.2f} KB/s | ETA: {remaining_time:.1f}s"
    )
    root.update_idletasks()

def download_video(url, path, choice):
    global start_time
    try:
        yt = YouTube(url, on_progress_callback=update_progress)
        title = sanitize_title(yt.title)

        if choice == "Video (MP4)":
            stream = yt.streams.get_highest_resolution()
        else:
            stream = yt.streams.filter(only_audio=True, file_extension="mp4").first()
            if not stream:
                stream = yt.streams.filter(only_audio=True, file_extension="webm").first()

        if not stream:
            messagebox.showerror("Error", "No stream found!")
            return

        start_time = time.time()
        stream.download(path, filename=title)
        messagebox.showinfo("Success", f"Downloaded: {title}")

    except Exception as e:
        messagebox.showerror("Error", str(e))

def start_download_single():
    url = url_box.get().strip()
    path = path_var.get()
    choice = format_choice.get()

    if not url or not path:
        messagebox.showerror("Error", "Please enter URL and choose folder")
        return

    Thread(target=download_video, args=(url, path, choice)).start()

def start_download_playlist():
    url = url_box.get().strip()
    path = path_var.get()
    choice = format_choice.get()

    if not url or not path:
        messagebox.showerror("Error", "Please enter Playlist URL and choose folder")
        return

    try:
        pl = Playlist(url)
        for video_url in pl.video_urls:
            Thread(target=download_video, args=(video_url, path, choice)).start()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        path_var.set(folder)

def load_video_info_single():
    url = url_box.get().strip()
    choice = format_choice.get()

    if not url:
        messagebox.showerror("Error", "Please enter a YouTube link!")
        return

    try:
        norm_url = normalize_youtube_url(url)
        yt = YouTube(norm_url)

        title = sanitize_title(yt.title)
        length = time.strftime("%M:%S", time.gmtime(yt.length))

        if choice == "Video (MP4)":
            stream = yt.streams.get_highest_resolution()
        else:
            stream = yt.streams.filter(only_audio=True, file_extension="mp4").first()
            if not stream:
                stream = yt.streams.filter(only_audio=True, file_extension="webm").first()

        size_mb = round(stream.filesize / 1024 / 1024, 2) if stream and stream.filesize else "?"

        # ---- Thumbnail ----
        thumb_url = yt.thumbnail_url
        response = requests.get(thumb_url)
        img_data = Image.open(BytesIO(response.content))
        img_data = img_data.resize((400, 225))
        img = ImageTk.PhotoImage(img_data)

        thumb_label.config(image=img)
        thumb_label.image = img

        title_label.config(text=f"🎬 {title}")
        info_label.config(text=f"⏳ Duration: {length}   |   💾 Size: {size_mb} MB")

        # Clickable thumbnail → open YouTube
        thumb_label.bind("<Button-1>", lambda e: webbrowser.open(norm_url))

    except Exception as e:
        messagebox.showerror("Error", f"Error: {e}")

# ---------- UI Layout ----------
def create_centered_label(parent, text, font_size=12, fg="white"):
    return Label(parent, text=text, bg="#1e1e1e", fg=fg, font=("Arial", font_size, "bold"))

# URL input
create_centered_label(scrollable_frame, "📺 Enter YouTube URL:", 12).pack(pady=8)
url_box = Entry(scrollable_frame, width=60, font=("Arial", 11))
url_box.pack(pady=5)

Button(scrollable_frame, text="🔍 Load Info", command=load_video_info_single, bg="#444", fg="white", relief="flat", width=15).pack(pady=5)

# Thumbnail & Info
thumb_label = Label(scrollable_frame, bg="#1e1e1e")
thumb_label.pack(pady=10)

title_label = create_centered_label(scrollable_frame, "", 13, "cyan")
title_label.pack(pady=3)

info_label = create_centered_label(scrollable_frame, "", 11, "lightgray")
info_label.pack(pady=3)

# Save folder
path_var = StringVar()
create_centered_label(scrollable_frame, "💾 Save to Folder:", 12).pack(pady=8)
Entry(scrollable_frame, textvariable=path_var, width=50, font=("Arial", 11)).pack(pady=5)
Button(scrollable_frame, text="📂 Browse", command=browse_folder, bg="#444", fg="white", relief="flat", width=12).pack(pady=5)

# Format dropdown
format_choice = StringVar(value="Video (MP4)")
ttk.Combobox(scrollable_frame, textvariable=format_choice, values=["Video (MP4)", "Audio (MP3)"], width=20, justify="center").pack(pady=8)

# Download buttons
Button(scrollable_frame, text="⬇️ Download Single Video", command=start_download_single, bg="#0066cc", fg="white", relief="flat", font=("Arial", 11, "bold"), width=25).pack(pady=8)
Button(scrollable_frame, text="📑 Download Playlist", command=start_download_playlist, bg="#009933", fg="white", relief="flat", font=("Arial", 11, "bold"), width=25).pack(pady=8)

# Progress
progress_var = DoubleVar()
progress_bar = ttk.Progressbar(scrollable_frame, variable=progress_var, maximum=100, length=600)
progress_bar.pack(pady=12)
progress_label = create_centered_label(scrollable_frame, "Progress: 0%", 11)
progress_label.pack()

root.mainloop()
