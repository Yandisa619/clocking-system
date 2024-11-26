import customtkinter as ctk
from tkinter import messagebox
import cv2
import face_recognition
import sqlite3
import numpy as np
from datetime import datetime
import time

# Database setup
conn = sqlite3.connect('clocking_system.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS clock_logs (
                      id INTEGER PRIMARY KEY,
                      user_id INTEGER,
                      clock_in_time TEXT,
                      clock_out_time TEXT
                 )''')

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                      user_id INTEGER PRIMARY KEY,
                      name TEXT,
                      face_encoding BLOB
                 )''')

cursor.execute("PRAGMA table_info(clock_logs)")
columns = [row[1] for row in cursor.fetchall()]
if "clock_out_time" not in columns:
    cursor.execute("ALTER TABLE clock_logs ADD COLUMN clock_out_time TEXT")
    conn.commit()

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
        ctk.CTkLabel(self.nav_frame, text="Navigation", font=("Poppins", 18, "bold")).pack(pady=20)
        nav_buttons = [
            ("Home", self.show_home_screen),
            ("Admin", self.show_admin_panel),
            ("Register User", self.show_registration_screen),
            ("Clock In", self.start_clock_in),
            ("View Logs", self.show_logs),
        ]
        for text, command in nav_buttons:
            ctk.CTkButton(self.nav_frame, text=text, command=command, height=40, width=180).pack(pady=10)

    def show_home_screen(self):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Welcome to the Clocking System", font=("Poppins", 24, "bold")).pack(pady=30)
        ctk.CTkLabel(self.content_frame, text="Use the navigation panel to get started.", font=("Poppins", 16)).pack()

    def show_admin_panel(self):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Admin Panel", font=("Poppins", 24, "bold")).pack(pady=20)

        users_frame = ctk.CTkScrollableFrame(self.content_frame, width=500, height=300)
        users_frame.pack(pady=10)

        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

        if not users:
            ctk.CTkLabel(users_frame, text="No users found.", font=("Poppins", 14)).pack(pady=20)
        else:
            for user in users:
                user_frame = ctk.CTkFrame(users_frame)
                user_frame.pack(pady=5, fill="x", padx=10)

                ctk.CTkLabel(user_frame, text=f"ID: {user[0]}, Name: {user[1]}", font=("Poppins", 14)).pack(side="left", padx=10)
                ctk.CTkButton(user_frame, text="Edit", command=lambda u=user: self.edit_user(u)).pack(side="left", padx=5)
                ctk.CTkButton(user_frame, text="Delete", command=lambda u=user: self.delete_user(u)).pack(side="left", padx=5)

        ctk.CTkButton(self.content_frame, text="Add User", command=self.show_registration_screen, width=200).pack(pady=20)

    def edit_user(self, user):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Edit User", font=("Poppins", 24, "bold")).pack(pady=20)

        name_entry = ctk.CTkEntry(self.content_frame, placeholder_text="Enter New Name", width=400)
        name_entry.insert(0, user[1])
        name_entry.pack(pady=10)

        def save_changes():
            new_name = name_entry.get()
            if new_name.strip():
                cursor.execute("UPDATE users SET name = ? WHERE user_id = ?", (new_name, user[0]))
                conn.commit()
                messagebox.showinfo("Success", "User updated successfully!")
                self.show_admin_panel()
            else:
                messagebox.showerror("Error", "Name cannot be empty.")

        ctk.CTkButton(self.content_frame, text="Save Changes", command=save_changes, width=200).pack(pady=20)

    def delete_user(self, user):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this user?"):
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user[0],))
            conn.commit()
            messagebox.showinfo("Success", "User deleted successfully!")
            self.show_admin_panel()

    def show_registration_screen(self):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Register User", font=("Poppins", 24, "bold")).pack(pady=20)
        name_entry = ctk.CTkEntry(self.content_frame, placeholder_text="Enter Name", width=400)
        name_entry.pack(pady=10)

        def capture_and_register():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Name cannot be empty.")
                return
            try:
                self.register_user(name)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to register user: {str(e)}")

        ctk.CTkButton(self.content_frame, text="Register", command=capture_and_register, width=200).pack(pady=20)

    def start_clock_in(self):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Clock In", font=("Poppins", 24, "bold")).pack(pady=20)
        ctk.CTkLabel(self.content_frame, text="Looking for faces...", font=("Poppins", 16)).pack(pady=10)
        self.clock_in()

    def clock_in(self):
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            messagebox.showerror("Camera Error", "Unable to access camera. Please check your device.")
            return

        messagebox.showinfo("Clock In", "Looking for faces. Please face the camera.")
        face_recognized = False

        known_face_encodings = self.known_face_encodings

        while True:
            ret, frame = video_capture.read()
            if not ret:
                messagebox.showerror("Camera Error", "Failed to read from the camera. Please try again.")
                break

            rgb_frame = frame[:, :, ::-1]
            face_locations = face_recognition.face_locations(rgb_frame)

            if face_locations:
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding)

                    if True in matches:
                        face_recognized = True
                        break

                    for (top, right, bottom, left) in face_locations:
                        cv2.rectangle(frame, (left, top), (right, bottom), (0,255,0), 2)
                    
                        if face_recognized or (cv2.waitKey(1) & 0xFF == ord ('q')):
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
        max_attempts = 10
        capture_time = 20
        attempt_counter = 0
        start_time = time.time()

        while attempt_counter < max_attempts:
            ret, frame = video_capture.read()
            if not ret:
                messagebox.showerror("Camera Error", f"Attempt {attempt_counter + 1}: Failed to read from the camera. Please try again.")
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)

            if face_locations:

                for (top, right, bottom, left) in face_locations:
                    cv2.rectangle(frame, (left, top), (right, bottom), (0,255,0), 2)
                
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                if len(face_encodings) > 0:
                    face_encoding = face_encodings[0]
                try:
                    cursor.execute("INSERT INTO users (name, face_encoding) VALUES (?, ?)", (name, face_encoding.tobytes()))
                    conn.commit()
                    self.known_face_encodings.append(face_encoding)
                    self.load_known_faces()
                    face_captured = True
                    break
                except Exception as e:
                    messagebox.showerror("Database Error", f"Failed to register face encoding: {str(e)}")
                    break

            cv2.imshow("Camera", frame)

            key = cv2.waitKey(1)

            if key == ord('q'):
                break

            attempt_counter +=1

            elapsed_time = time.time() - start_time
            if elapsed_time >= capture_time:
                retry = messagebox.askretrycancel("Timeout", "Face capture timed out. Please try again.")
            if retry:
                start_time = time.time()
                attempt_counter = 0
            
            else:
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
        for user_id, face_encoding in cursor.fetchall():
            self.known_face_ids.append(user_id)
            self.known_face_encodings.append(np.frombuffer(face_encoding, dtype=np.float64))

    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_logs(self):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Clocking Logs", font=("Poppins", 24, "bold")).pack(pady=20)
        logs_frame = ctk.CTkScrollableFrame(self.content_frame, width=500, height=300)
        logs_frame.pack(pady=10)

        cursor.execute("SELECT * FROM clock_logs")
        logs = cursor.fetchall()

        if not logs:
            ctk.CTkLabel(logs_frame, text="No logs found.", font=("Poppins", 14)).pack(pady=20)
        else:
            for log in logs:
                log_text = f"User ID: {log[1]}, Clock-In: {log[2]}, Clock-Out: {log[3]}"
                ctk.CTkLabel(logs_frame, text=log_text, font=("Poppins", 14)).pack(anchor="w", padx=10)

        ctk.CTkButton(self.content_frame, text="Refresh Logs", command=self.show_logs, width=200).pack(pady=20)


if __name__ == "__main__":
    app = ClockingApp()
    app.mainloop()
