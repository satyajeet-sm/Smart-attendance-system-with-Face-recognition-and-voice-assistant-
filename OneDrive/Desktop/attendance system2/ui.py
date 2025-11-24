import customtkinter as ctk
from PIL import Image, ImageTk
from customtkinter import CTkImage
import threading
import cv2
import time
import speech_recognition as sr
from backend import enroll_face, recognize_face, get_attendance_summary, speak


# SMART AI ATTENDANCE SYSTEM (UI)
# App Setup

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("🤖 Smart AI Attendance System")
app.geometry("1000x700")


# Header

header = ctk.CTkLabel(
    app,
    text="Smart AI Attendance System",
    font=ctk.CTkFont(size=28, weight="bold")
)
header.pack(pady=15)


# Main Frames

content_frame = ctk.CTkFrame(app, corner_radius=15)
content_frame.pack(padx=20, pady=10, fill="both", expand=True)

left_frame = ctk.CTkFrame(content_frame, width=600, corner_radius=15)
left_frame.pack(side="left", padx=20, pady=20, fill="both", expand=True)

right_frame = ctk.CTkFrame(content_frame, width=300, corner_radius=15)
right_frame.pack(side="right", padx=20, pady=20, fill="y")


# CAMERA SETUP

camera_label = ctk.CTkLabel(left_frame, text="Camera Preview", font=ctk.CTkFont(size=18))
camera_label.pack(pady=10)

video_label = ctk.CTkLabel(left_frame, text="")
video_label.pack(pady=10, fill="both", expand=True)

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
camera_active = True


def show_camera():
    """Display live camera feed using CTkImage (no DPI warning)."""
    if camera_active and cap.isOpened():
        ret, frame = cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)

            # Convert to CTkImage
            ctk_img = CTkImage(light_image=img, size=(600, 400))
            video_label.configure(image=ctk_img)
            video_label.image = ctk_img  # prevent garbage collection

    app.after(30, show_camera)

threading.Thread(target=show_camera, daemon=True).start()


# STATUS BAR

status_label = ctk.CTkLabel(left_frame, text="System Ready ✅", font=ctk.CTkFont(size=16))
status_label.pack(pady=10)


def update_status(msg):
    """Update status message on the UI."""
    status_label.configure(text=f"🧠 {msg}")
    print(f"[STATUS] {msg}")


# VOICE COMMANDS

stop_listening_flag = False


def take_command():
    """Capture and recognize speech input."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("[STATUS] Listening 🎤...")
        r.pause_threshold = 1
        audio = r.listen(source, phrase_time_limit=5)
    try:
        print("[STATUS] Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        print(f"[YOU SAID] {query}")
    except sr.UnknownValueError:
        print("[ERROR] Could not understand audio.")
        return ""
    except sr.RequestError:
        print("[ERROR] Could not connect to speech service.")
        return ""
    return query.lower()


def voice_commands():
    """Continuously listen and respond to voice commands."""
    speak("Say start to activate voice commands.")
    print("[STATUS] Say 'start' to activate voice commands 🎤")
    global stop_listening_flag
    while not stop_listening_flag:
        query = take_command()
        if not query:
            continue

        if 'start' in query:
            speak("Starting Smart AI Attendance System.")
            print("[AI] Starting Smart AI Attendance System...")
            recognize_face()

        elif 'enroll' in query:
            speak("Enrolling new face.")
            enroll_face()

        elif 'summary' in query or 'attendance' in query:
            speak("Fetching attendance summary.")
            get_attendance_summary()

        elif 'stop' in query or 'exit' in query or 'shutdown' in query:
            speak("Shutting down Smart AI Attendance System.")
            print("[AI] System shutting down...")
            stop_listening_flag = True
            break

        time.sleep(0.1)


threading.Thread(target=voice_commands, daemon=True).start()


# BUTTONS

button_font = ctk.CTkFont(size=16, weight="bold")

ctk.CTkButton(
    right_frame, text="🧍 Enroll Face", font=button_font,
    command=lambda: threading.Thread(target=enroll_face, daemon=True).start()
).pack(pady=15, fill="x")

ctk.CTkButton(
    right_frame, text="🎯 Recognize Face", font=button_font,
    command=lambda: threading.Thread(target=recognize_face, daemon=True).start()
).pack(pady=15, fill="x")

ctk.CTkButton(
    right_frame, text="📊 Attendance Summary", font=button_font,
    command=lambda: threading.Thread(
        target=lambda: speak(
            "\n".join([f"{u}: {d} times" for u, d in get_attendance_summary()])
            if get_attendance_summary() else "No attendance yet."
        ),
        daemon=True
    ).start()
).pack(pady=15, fill="x")

ctk.CTkButton(
    right_frame, text="🚪 Exit", font=button_font, fg_color="red",
    command=lambda: threading.Thread(target=lambda: exit_app(), daemon=True).start()
).pack(pady=25, fill="x")


#  EXIT HANDLER

def exit_app():
    """Safely exit the app and release resources."""
    global camera_active, stop_listening_flag
    camera_active = False
    stop_listening_flag = True
    if cap.isOpened():
        cap.release()
    speak("Shutting down Smart AI Attendance System.")
    update_status("System shutting down...")
    time.sleep(1)
    app.quit()


# Footer

footer = ctk.CTkLabel(
    app,
    text="smart attendence system 💻",
    font=ctk.CTkFont(size=14, slant="italic")
)
footer.pack(side="bottom", pady=10)

app.protocol("WM_DELETE_WINDOW", exit_app)
app.mainloop()

