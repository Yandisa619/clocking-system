import customtkinter as ctk
import cv2
import face_recognition
import sqlite3
import numpy as np
from PIL import Image, ImageTk
from tkinter import messagebox

# Database setup
conn = sqlite3.connect('face_recognition.db')
cursor = conn.cursor()

# Create a table for storing users and their face encodings
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT,
                    face_encoding BLOB
                 )''')
conn.commit()

# Initialize the CustomTkinter window
class FaceRecognitionApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Admin Face Recognition Login")
        self.geometry("900x600")
        self.configure(padx=20, pady=20)

        # Store known face encodings
        self.known_face_encodings = []
        self.known_face_ids = []
        self.load_known_faces()

        # Navigation Frame
        self.nav_frame = ctk.CTkFrame(self, width=200)
        self.nav_frame.grid(row=0, column=0, sticky="ns", padx=10, pady=10)
        self.create_nav_buttons()

        # Content Frame
        self.content_frame = ctk.CTkFrame(self, width=600)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.show_home_screen()

        # Set grid weights for resizing
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def create_nav_buttons(self):
        ctk.CTkLabel(self.nav_frame, text="Navigation", font=("Arial", 18, "bold")).pack(pady=20)
        nav_buttons = [
            ("Home", self.show_home_screen),
            ("Register Admin Face", self.register_admin),
            ("Admin Login", self.admin_login)
        ]
        for text, command in nav_buttons:
            ctk.CTkButton(self.nav_frame, text=text, command=command, height=40, width=180).pack(pady=10)

    def show_home_screen(self):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Welcome to the Admin Face Recognition System", font=("Arial", 24, "bold")).pack(pady=30)
        ctk.CTkLabel(self.content_frame, text="Use the navigation panel to get started.", font=("Arial", 16)).pack()

    def register_admin(self):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Admin Face Registration", font=("Arial", 24, "bold")).pack(pady=30)

        # Start the camera for face registration
        self.capture_face("admin")

    def admin_login(self):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Admin Login", font=("Arial", 24, "bold")).pack(pady=30)

        # Start the camera for face recognition
        self.authenticate_face()

    def capture_face(self, user_type="admin"):
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            messagebox.showerror("Camera Error", "Unable to access the camera. Please check your device.")
            return

        messagebox.showinfo("Face Capture", f"Look at the camera to register your {user_type} face.")

        # Create a label to display the video feed
        self.camera_label = ctk.CTkLabel(self.content_frame)
        self.camera_label.pack(pady=20)

        face_captured = False
        while True:
            ret, frame = video_capture.read()
            if not ret:
                messagebox.showerror("Camera Error", "Failed to read from the camera. Please try again.")
                break

            # Convert the frame to RGB (OpenCV uses BGR by default)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Detect faces in the frame
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            # If faces are detected, capture the first face encoding
            if face_encodings:
                face_encoding = face_encodings[0]

                # Save the face encoding into the database
                cursor.execute("INSERT INTO users (name, face_encoding) VALUES (?, ?)", (user_type.capitalize(), face_encoding.tobytes()))
                conn.commit()
                messagebox.showinfo("Registration Successful", f"{user_type.capitalize()} face registered successfully!")

                # Load known faces into memory
                self.load_known_faces()

                face_captured = True
                break

            # Convert the frame into a PhotoImage object to update the GUI
            img = Image.fromarray(rgb_frame)
            img_tk = ImageTk.PhotoImage(img)
            self.camera_label.configure(image=img_tk)
            self.camera_label.image = img_tk

            # Exit if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()

        if not face_captured:
            messagebox.showerror("Face Not Detected", "No face detected. Please try again.")

    def authenticate_face(self):
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            messagebox.showerror("Camera Error", "Unable to access the camera. Please check your device.")
            return

        messagebox.showinfo("Face Authentication", "Looking for your face...")

        # Create a label to display the video feed
        self.camera_label = ctk.CTkLabel(self.content_frame)
        self.camera_label.pack(pady=20)

        authenticated = False
        while True:
            ret, frame = video_capture.read()
            if not ret:
                messagebox.showerror("Camera Error", "Failed to read from the camera. Please try again.")
                break

            # Convert the frame to RGB (OpenCV uses BGR by default)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Detect faces in the frame
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)

                # Check if face matches the admin's face
                if True in matches:
                    match_index = matches.index(True)
                    user_id = self.known_face_ids[match_index]

                    # Check if the matched face belongs to the admin (user_id == 1)
                    if user_id == 1:
                        authenticated = True
                        break

            # Convert the frame into a PhotoImage object to update the GUI
            img = Image.fromarray(rgb_frame)
            img_tk = ImageTk.PhotoImage(img)
            self.camera_label.configure(image=img_tk)
            self.camera_label.image = img_tk

            # Exit if 'q' is pressed or if admin is authenticated
            if cv2.waitKey(1) & 0xFF == ord('q') or authenticated:
                break

        video_capture.release()

        if authenticated:
            messagebox.showinfo("Login Successful", "Admin recognized. Welcome!")
            self.show_home_screen()  # Redirect to home after login
        else:
            messagebox.showwarning("Login Failed", "No recognized face. Please try again.")

    def load_known_faces(self):
        self.known_face_ids = []
        self.known_face_encodings = []

        # Load the admin's registered face from the database
        cursor.execute("SELECT user_id, face_encoding FROM users WHERE user_id = 1")
        result = cursor.fetchone()

        if result:
            # Load the admin's face encoding into memory
            user_id, face_encoding_blob = result
            face_encoding = np.frombuffer(face_encoding_blob, dtype=np.float64)
            self.known_face_ids.append(user_id)
            self.known_face_encodings.append(face_encoding)

    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

# Run the application
app = FaceRecognitionApp()
app.mainloop()

