import cv2
import face_recognition
import numpy as np
import os
import pickle
import sqlite3
import pyttsx3
import time
from datetime import datetime
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder, StandardScaler
import speech_recognition as sr


#  Speech Setup

engine = pyttsx3.init()
engine.setProperty('rate', 160)

def speak(text):
    print(f"[AI] {text}")
    engine.say(text)
    engine.runAndWait()


#  Database Setup

DB_PATH = 'attendance.db'
ENCODINGS_PATH = 'encodings.pkl'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS attendance (
                    name TEXT,
                    timestamp TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

#  Face Data Handling

if os.path.exists(ENCODINGS_PATH):
    with open(ENCODINGS_PATH, 'rb') as f:
        data = pickle.load(f)
    known_encodings = data['encodings']
    known_names = data['names']
else:
    known_encodings, known_names = [], []


#  Model Setup

svm_model = None
scaler = None
label_encoder = None

def train_model():
    global svm_model, scaler, label_encoder
    if not known_encodings:
        svm_model = None
        return

    X = np.array(known_encodings)
    y = np.array(known_names)

    # Prevent training on only one class
    if len(set(y)) < 2:
        print("[INFO] Not enough unique faces to train model (need ≥2).")
        svm_model = None
        return

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    svm_model = SVC(kernel='linear', probability=True)
    svm_model.fit(X_scaled, y_encoded)
train_model()


#  Enroll New Face

def enroll_face():
    speak("Please look at the camera for enrollment.")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    time.sleep(1)

    ret, frame = cap.read()
    if not ret:
        speak("Camera error. Try again.")
        cap.release()
        return

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = face_recognition.face_locations(rgb)

    if not faces:
        speak("No face detected. Try again.")
        cap.release()
        return

    encoding = face_recognition.face_encodings(rgb, faces)[0]
    cap.release()

    # 🎤 Voice input for name
    r = sr.Recognizer()
    name = "Unknown"
    try:
        with sr.Microphone() as source:
            speak("Say your name now.")
            r.adjust_for_ambient_noise(source, duration=1)
            audio = r.listen(source, timeout=8, phrase_time_limit=5)
            name = r.recognize_google(audio).capitalize()
    except:
        speak("Could not understand your name.")
        return

    # Save face data
    known_encodings.append(encoding)
    known_names.append(name)

    with open(ENCODINGS_PATH, 'wb') as f:
        pickle.dump({'encodings': known_encodings, 'names': known_names}, f)

    train_model()
    speak(f"{name} enrolled successfully!")


#  Recognize Face

def recognize_face():
    if not known_encodings:
        speak("No registered users found.")
        return None

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    speak("Recognizing face. Please look at the camera.")
    time.sleep(1)

    ret, frame = cap.read()
    cap.release()

    if not ret:
        speak("Camera error.")
        return None

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = face_recognition.face_locations(rgb)

    if not faces:
        speak("No face detected.")
        return None

    encoding = face_recognition.face_encodings(rgb, faces)[0]

    if svm_model is None:
        speak("Model not trained yet.")
        return None

    X_scaled = scaler.transform([encoding])
    y_pred = svm_model.predict(X_scaled)
    name = label_encoder.inverse_transform(y_pred)[0]

    mark_attendance(name)
    speak(f"Welcome {name}. Attendance marked.")
    return name


#  Attendance System

def mark_attendance(name):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO attendance VALUES (?, ?)", 
                (name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_attendance_summary():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name, COUNT(*) FROM attendance GROUP BY name")
    data = cur.fetchall()
    conn.close()

    if not data:
        speak("No attendance records found.")
        return []

    summary = "Attendance Summary:\n"
    for name, count in data:
        summary += f"{name}: {count} times\n"

    speak(summary)
    return data
