import customtkinter as ctk
from tkinter import messagebox
import cv2
import face_recognition
import sqlite3
import numpy as np
from datetime import datetime

# Database setup
conn = sqlite3.connect('clocking_system.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS clock_logs (
                      id INTEGER PRIMARY KEY,
                      user_id INTEGER,
                      clock_in_time TEXT
                 )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                      user_id INTEGER PRIMARY KEY,
                      name TEXT,
                      face_encoding BLOB
                 )''')

# Initialize CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ClockingApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Advanced Clocking System")
        self.geometry("900x600")
        self.configure(padx=20, pady=20)

        # Known faces and IDs
        self.known_face_encodings = []
        self.known_face_ids = []
        self.load_known_faces()

        # Navigation frame
        self.nav_frame = ctk.CTkFrame(self, width=200)
        self.nav_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=10)
        self.create_nav_buttons()

        # Content frame
        self.content_frame = ctk.CTkFrame(self, width=600)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.show_home_screen()

        # Set grid weights
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def create_nav_buttons(self):
        ctk.CTkLabel(self.nav_frame, text="Navigation", font=("Arial", 18, "bold")).pack(pady=20)
        nav_buttons = [
            ("Home", self.show_home_screen),
            ("Register User", self.show_registration_screen),
            ("Clock In", self.start_clock_in),
            ("View Logs", self.show_logs),
        ]
        for text, command in nav_buttons:
            ctk.CTkButton(self.nav_frame, text=text, command=command, height=40, width=180).pack(pady=10)

    def show_home_screen(self):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Welcome to the Clocking System", font=("Arial", 24, "bold")).pack(pady=30)
        ctk.CTkLabel(self.content_frame, text="Use the navigation panel to get started.", font=("Arial", 16)).pack()

    def show_registration_screen(self):
        self.clear_content_frame()

        ctk.CTkLabel(self.content_frame, text="Register User", font=("Arial", 24, "bold")).pack(pady=20)
        name_entry = ctk.CTkEntry(self.content_frame, placeholder_text="Enter Name", width=400)
        name_entry.pack(pady=10)

        def capture_and_register():
            name = name_entry.get()
            if name.strip():
                self.register_user(name)
                messagebox.showinfo("Success", "User registered successfully!")
            else:
                messagebox.showerror("Error", "Name cannot be empty.")

        ctk.CTkButton(self.content_frame, text="Capture & Register", command=capture_and_register, width=200).pack(pady=20)

    def start_clock_in(self):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Clock In", font=("Arial", 24, "bold")).pack(pady=20)
        ctk.CTkLabel(self.content_frame, text="Looking for faces...", font=("Arial", 16)).pack(pady=10)
        self.clock_in()

    def clock_in(self):
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            messagebox.showerror("Camera Error", "Unable to access camera. Please check your device.")
            return

        messagebox.showinfo("Clock In", "Looking for faces. Please face the camera.")
        face_recognized = False

        while True:
            ret, frame = video_capture.read()
            if not ret:
                messagebox.showerror("Camera Error", "Failed to read from the camera. Please try again.")
                break

            rgb_frame = frame[:, :, ::-1]
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                if True in matches:
                    match_index = matches.index(True)
                    user_id = self.known_face_ids[match_index]
                    self.log_clock_in(user_id)  
                    face_recognized = True
                    break

            
            cv2.imshow("Camera - Press Q to Quit", frame)

            if face_recognized or (cv2.waitKey(1) & 0xFF == ord('q')):
                break

        
        video_capture.release()
        cv2.destroyAllWindows()

        if face_recognized:
            messagebox.showinfo("Clock In Success", "Face recognized. Clock-in recorded!")
        else:
            messagebox.showwarning("Clock In Failed", "No recognized face. Please try again.")

    def register_user(self, name):
        video_capture = cv2.VideoCapture(0)  
        if not video_capture.isOpened():
            messagebox.showerror("Camera Error", "Unable to access the camera. Please check your device.")
            return

        messagebox.showinfo("Camera Active", "Look at the camera. Capturing your face...")
        face_captured = False

        while True:
            ret, frame = video_capture.read()
            if not ret:
                messagebox.showerror("Camera Error", "Failed to read from the camera. Please try again.")
                break

            rgb_frame = frame[:, :, ::-1]
            face_locations = face_recognition.face_locations(rgb_frame)

            if face_locations:
                
                face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]

                
                cursor.execute("INSERT INTO users (name, face_encoding) VALUES (?, ?)", (name, face_encoding.tobytes()))
                conn.commit()

                
                self.load_known_faces()
                face_captured = True
                break

            
            cv2.imshow("Camera - Press Q to Quit", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        
        video_capture.release()
        cv2.destroyAllWindows()

        if face_captured:
            messagebox.showinfo("Success", "Face registered successfully!")
        else:
            messagebox.showerror("Face Not Detected", "No face detected. Please try again.")

    def load_known_faces(self):
        self.known_face_ids = []
        self.known_face_encodings = []

        cursor.execute("SELECT user_id, face_encoding FROM users")
        for user_id, face_encoding_blob in cursor.fetchall():
            face_encoding = np.frombuffer(face_encoding_blob, dtype=np.float64)
            self.known_face_ids.append(user_id)
            self.known_face_encodings.append(face_encoding)

    def log_clock_in(self, user_id):
        time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO clock_logs (user_id, clock_in_time) VALUES (?, ?)", (user_id, time_now))
        conn.commit()
        messagebox.showinfo("Clock In Successful", f"User {user_id} clocked in at {time_now}")

    def show_logs(self):
        self.clear_content_frame()

        ctk.CTkLabel(self.content_frame, text="Clock Logs", font=("Arial", 24, "bold")).pack(pady=20)
        logs_frame = ctk.CTkScrollableFrame(self.content_frame, width=500, height=300)
        logs_frame.pack(pady=10)

        cursor.execute("SELECT * FROM clock_logs")
        logs = cursor.fetchall()
        if not logs:
            messagebox.showinfo("Info", "No logs available.")
            return

        for log in logs:
            ctk.CTkLabel(logs_frame, text=f"User {log[1]} - {log[2]}", font=("Arial", 14)).pack(anchor="w", pady=5)

    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()


app = ClockingApp()
app.mainloop()
