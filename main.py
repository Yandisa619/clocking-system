import customtkinter as ctk
from tkinter import messagebox, StringVar, OptionMenu, filedialog
from datetime import datetime
from reportlab.lib.pagesizes import letter 
from reportlab.pdfgen import canvas
import cv2
import face_recognition
import sqlite3
import numpy as np
import time
import os
import subprocess

# Database setup
conn = sqlite3.connect('clocking_system.db')
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON")
cursor.execute('''CREATE TABLE IF NOT EXISTS clock_logs (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER NOT NULL,
                      clock_in_time TEXT NOT NULL,
                      clock_out_time TEXT,
                      FOREIGN KEY (user_id) REFERENCES users(user_id)
                          ON DELETE CASCADE ON UPDATE CASCADE
                 )''')

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                      user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL,
                      face_encoding BLOB NOT NULL,
                      emp_number TEXT,
                      gender TEXT,
                      occupation TEXT
                 )''')

cursor.execute("PRAGMA table_info(clock_logs)")
columns = [row[1] for row in cursor.fetchall()]
if "clock_out_time" not in columns:
    cursor.execute("ALTER TABLE clock_logs ADD COLUMN clock_out_time TEXT")
    conn.commit()

cursor.execute("PRAGMA table_info(users)")
columns = [row[1] for row in cursor.fetchall()]

if "emp_number" not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN emp_number TEXT")
if "gender" not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN gender TEXT")
if "occupation" not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN occupation TEXT")

    conn.commit()

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON clock_logs(user_id)')


# Initialize CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ClockingApp(ctk.CTk):
    def __init__(self, conn):
        super().__init__()
        self.title("Advanced Clocking System")
        self.geometry("900x600")
        self.configure(padx=20, pady=20)

        # Known faces and IDs
        self.conn = conn
        self.known_face_encodings = []
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
        ctk.CTkLabel(self.nav_frame, text="Navigation", font=("Poppins", 20, "bold"), text_color = "#1E90FF").pack(pady = (30, 20))
        nav_buttons = [
            ("🏠 Home", self.show_home_screen),
            ("🔧 Admin", self.show_admin_panel),
            (" 📝 Register User", self.show_registration_screen),
            (" 🕒 Clock In", self.start_clock_in),
            (" ⏰ Clock Out", self.clock_out),
            (" 📜 View Logs", self.show_logs),
            (" 🚪 Log Out", self.logout),
        ]
        for text, command in nav_buttons:
            ctk.CTkButton(self.nav_frame, text=text, command=command, height=40, width=180, corner_radius = 10, fg_color = "#1E90FF", hover_color = "#4682B4", text_color = "white", font = ("Poppins", 14)).pack(pady = (10, 20))

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
        ctk.CTkButton(self.content_frame, text="Logout", command=self.logout, width=200).pack(pady=20)


    def edit_user(self, user):
        self.clear_content_frame()
        ctk.CTkLabel(self.content_frame, text="Edit User", font=("Poppins", 24, "bold")).pack(pady=20)
        
        # Name Entry
        ctk.CTkLabel(self.content_frame, text="Enter New Name", font=("Poppins", 14, "bold")).pack(pady=(10, 20))
        name_entry = ctk.CTkEntry(self.content_frame, placeholder_text="Enter New Name", width=200)
        name_entry.insert(0, user[1])
        name_entry.pack(pady = (0, 20))

        # Employee Number Entry
        ctk.CTkLabel(self.content_frame, text="Employee Number", font=("Poppins", 14, "bold")).pack(pady=(10, 20))
        emp_number_entry = ctk.CTkEntry(self.content_frame, placeholder_text="Enter Employee Number", width=200)
        emp_number_entry.insert(0, user[3]) 
        emp_number_entry.pack(pady=(0, 20))
        emp_number_entry.configure(state="readonly")

        # Gender Dropdown
        ctk.CTkLabel(self.content_frame, text="Gender", font=("Poppins", 14, "bold")).pack(pady=(10, 20))
        gender_var = StringVar(value=user[4])
        gender_menu = ctk.CTkOptionMenu(self.content_frame, values=["Male", "Female", "Other"], variable=gender_var, width=200)
        gender_menu.pack(pady=(0, 20))

        # Occupational Dropdown
        ctk.CTkLabel(self.content_frame, text="Occupation", font=("Poppins", 14, "bold")).pack(pady=(10, 20))
        occupation_var = StringVar(value=user[5])
        occupation_menu = ctk.CTkOptionMenu(self.content_frame, values=["Software Candidate", "Networks Candidate", "Other"], variable=occupation_var, width=200)
        occupation_menu.pack(pady=(0, 20))

        def update_picture():
            video_capture = cv2.VideoCapture(0)
            if not video_capture.isOpened():
                messagebox.showerror("Camera Error", "Unable to access the camera. Please check your device.")
                return 
            messagebox.showinfo("Camera Active", "Look at the camera. Capturing your new face picture...")

            face_captured = False 
            while True:
                ret, frame = video_capture.read()
                if not ret:
                    messagebox.showerror("Camera Error", "Failed to read from the camera. Please try again.")
                    break

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame, model="hog")

                if face_locations:
                    for (top, right, bottom, left) in face_locations:
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                    if len(face_encodings) > 0:
                       face_encoding = face_encodings[0]
                       encoded_face = face_encoding.tobytes()
                       
                       cursor = self.conn.cursor()
                       cursor.execute("UPDATE users SET face_encoding = ? WHERE user_id = ?", (encoded_face, user[0]))
                       self.conn.commit()

                       self.load_known_faces()

                       messagebox.showinfo("Success", "Face picture replaced successfully!")
                       face_captured = True
                       break
                    cv2.imshow("Update Picture - User Registration", frame)

                    key = cv2.waitKey(1)
                    if key == ord('q'):
                        break 

                    video_capture.release()
                    cv2.destroyAllWindows()
        
        def save_changes():
            new_name = name_entry.get()
            new_gender = gender_var.get()
            new_occupation = occupation_var.get()
            
            if not new_name.strip():
                messagebox.showerror("Error", "Name cannot be empty.")
                return
            
            if new_gender == "Select Gender" or new_occupation == "Select Occupation":
               messagebox.showerror("Error", "Please select both Gender and Occupation.")
               return

            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE users
                SET name = ?, gender = ?, occupation = ?
                WHERE user_id = ?''', (new_name, new_gender, new_occupation, user[0]))
            self.conn.commit()
            self.show_admin_panel()
        
        ctk.CTkButton(self.content_frame, text="Update Picture", command=update_picture, width=200).pack(pady=10)
        ctk.CTkButton(self.content_frame, text="Save Changes", command=save_changes, width=200).pack(pady=20)
    
    # Logout Button
    def logout(self):
        if hasattr(self, 'after_id') and self.after_id is not None:
            self.after_cancel(self.after_id)
        
        messagebox.showinfo("Logout", "You have been logged out successfully.")
        
        self.current_user = None
        self.destroy()

        registration_screen_path = r"C:\Users\CAPACITI\OneDrive - EOH\Documents\clocking-system\Register.py"
        subprocess.Popen(["python", registration_screen_path])

    def delete_user(self, user):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this user?"):
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user[0],))
            conn.commit()
            messagebox.showinfo("Success", "User deleted successfully!")
            self.show_admin_panel()

    def show_registration_screen(self):
        self.clear_content_frame()
       
       # Name Entry
        ctk.CTkLabel(self.content_frame, text="Register User", font=("Poppins", 14, "bold")).pack(pady= (10, 20))
        name_entry = ctk.CTkEntry(self.content_frame, placeholder_text="Enter Name", width=200)
        name_entry.pack(pady= (0, 20))

        # Employee Number Entry 
        ctk.CTkLabel(self.content_frame, text="Employee Number", font=("Poppins", 14, "bold")).pack(pady= (10, 20))
        emp_number_entry = ctk.CTkEntry(self.content_frame, placeholder_text="Enter Employee Number", width=200)
        emp_number_entry.pack(pady= (0, 20))

        # Gender
        ctk.CTkLabel(self.content_frame, text = "Gender", font = ("Poppins", 14, "bold")).pack(pady = (10, 20))
        gender_var = StringVar(value = "Select Gender")
        gender_menu = ctk.CTkOptionMenu(self.content_frame, values=["Male", "Female", "Other"], variable=gender_var, width = 200)
        gender_menu.pack(pady = (0, 20))

        # Occupation Dropdown
        ctk.CTkLabel(self.content_frame, text = "Occupation", font = ("Poppins", 14, "bold")).pack(pady = (10,20))
        occupation_var = StringVar(value = "Select Occupation")
        occupation_menu = ctk.CTkOptionMenu(self.content_frame, values=["Software Candidate", "Networks Candidate", "Other"], variable=occupation_var, width = 200)
        occupation_menu.pack(pady = (0, 20))
        
        # User Input validation
        def validate_registration_inputs(name, emp_number, gender, occupation):
            if not name or not name.replace(" ","").isalpha():
               messagebox.showerror("Error", "Invalid name. Please enter a valid name.")
               return False 
        
            if not emp_number or not emp_number.isalnum():
               messagebox.showerror("Error", "Invalid employee number. It must be alphanumeric.")
               return False

            if gender not in ["Male", "Female", "Other"]:
               messagebox.showerror("Error", "Please select a valid gender.")
               return False

            if occupation not in ["Software Candidate", "Networks Candidate", "Other"]:
               messagebox.showerror("Error", "Please select a valid occupation.")
               return False
            return True

        def capture_and_register():
            name = name_entry.get().strip()
            emp_number = emp_number_entry.get().strip()
            gender = gender_var.get()
            occupation = occupation_var.get()
            
            if not validate_registration_inputs(name, emp_number, gender, occupation):
                return 
              
            try:
                conn = sqlite3.connect("clocking_system.db")
                self.register_user(name, emp_number, gender, occupation, conn)
                messagebox.showinfo("Success", "User registered successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to register user: {str(e)}")
            finally:
                conn.close()

        ctk.CTkButton(self.content_frame, text="Register", command=capture_and_register, width=200).pack(pady=20)
    
    def record_clock_in(self, user_id):
        cursor = self.conn.cursor()
        clock_in_time = time.strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''INSERT INTO clock_logs (user_id, clock_in_time)
                          VALUES (?,?)''', (user_id, clock_in_time))

        self.conn.commit()
        messagebox.showinfo("Clock In Success", f"User {user_id} clocked in at {clock_in_time}.")

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
        start_time = time.time()
        max_duration = 30

        time.sleep(2)

        

        while True:
           ret, frame = video_capture.read()
           if not ret:
            messagebox.showerror("Camera Error", "Failed to read from the camera. Please try again.")
            break
           
           elapsed_time = time.time() - start_time
           remaining_time = max_duration - elapsed_time

           if remaining_time <= 0:
            messagebox.showwarning("Clock In Timeout", "Time exceeded. Please try again.")
            break
       

           rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
           face_locations = face_recognition.face_locations(rgb_frame, model="hog")
            
           for top, right, bottom, left in face_locations:
               cv2.rectangle(frame, (left, top), (right, bottom), (0, 255,0), 2)
            
           cv2.putText(frame, f"Time left:{int(remaining_time)} seconds", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA, )
            
           
           cv2.imshow("Camera Feed - Press Q to Exit", frame)
         

           face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
 
           for face_encoding in face_encodings:  
               matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.55)
               if True in matches:
                matched_index = matches.index(True)
                user_id = self.known_face_ids[matched_index]
                messagebox.showinfo("Clock In Success", f"User ID {user_id} recognized. Clock-in recorded!")
                self.record_clock_in(user_id)
                face_recognized = True
                break

           if face_recognized or (cv2.waitKey(1) & 0xFF == ord('q')):
            break
 
           video_capture.release()
           cv2.destroyAllWindows()

        if not face_recognized:
         messagebox.showwarning("Clock In Failed", "No recognized face. Please try again.")

    def clock_out(self):
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            messagebox.showerror("Camera Error", "Unable to access camera. Please check your device.")
            return

        messagebox.showinfo("Clock Out", "Looking for faces to clock out. Please face the camera.")
        face_recognized = False
        retries = 0
        start_time = time.time()
        max_duration = 30

        time.sleep(1)

        while True:
            ret, frame = video_capture.read()
            if not ret:
               retries +=1
               print("Camera Error", "No faces detected, You have 3 attempts left.")
               if retries >= 3:
                  print("Camera Error", "Unable to capture video after multiple attempts.")
                  break
               continue

            retries = 0

            elapsed_time = time.time() - start_time
            if elapsed_time > max_duration:  
             messagebox.showwarning("Clock Out Timeout", "Time exceeded. Please try again.")
             break

            
            

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            face_locations = face_recognition.face_locations(rgb_frame, model="hog")

            if not face_locations:
                print("Camera Error", "No faces detected.")
                continue
            
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for face_encoding in face_encodings:
                 matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.55)
                 if True in matches:
                    matched_index = matches.index(True)
                    user_id = self.known_face_ids[matched_index]
                    messagebox.showinfo("Clock Out Success", f"User ID {user_id} recognized. Clock-out recorded!")

                    self.record_clock_out(user_id)
                    face_recognized = True
                    break

                 if face_recognized or (cv2.waitKey(1) & 0xFF == ord('q')):
                    break

            video_capture.release()
            cv2.destroyAllWindows()

            if not face_recognized:
                messagebox.showwarning("Clock Out Failed", "No recognized face. Please try again.")
    
    def record_clock_out(self, user_id):   
        clock_out_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id FROM clock_logs
            WHERE user_id = ? AND clock_out_time IS NULL
            ORDER BY clock_in_time DESC LIMIT 1''', (user_id,))

        clock_in_record = cursor.fetchone()

        if clock_in_record:

            cursor.execute('''
                UPDATE clock_logs
                SET clock_out_time = ?
                WHERE id = ?''', (clock_out_time, clock_in_record[0]))
            self.conn.commit()
            messagebox.showinfo("Clock Out Success", "Clock-out time recorded successfully!")
        else:
            messagebox.showwarning("Clock Out Failed", "No active clock-in record found for this user.")
 

    

    def load_known_faces(self):
        self.known_face_encodings = []
        self.known_face_ids = []
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id, face_encoding FROM users")
        results = cursor.fetchall()

        for row in results:
            user_id, encoding_blob = row
            if encoding_blob is not None:
                try:
                  encoding = np.frombuffer(row[1], dtype=np.float64) 
                  if encoding.shape == (128,):
                    self.known_face_encodings.append(encoding)
                    self.known_face_ids.append(user_id) 
                except Exception as e:
                    messagebox.showerror(f"Error loading face encoding for user_id {row[0]}: {e}")  

        
    #Face Registration Validation 
    def is_face_duplicate(self, face_encoding):
       matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.55)
       return True in matches
    
    def register_user(self, name, emp_number, gender, occupation, conn):
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            messagebox.showerror("Camera Error", "Unable to access the camera. Please check your device.")
            return

        messagebox.showinfo("Camera Active", "Look at the camera. Capturing your face...")
        face_captured = False

        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE name = ?", (name,))
        user = cursor.fetchone()
        
        if user:
            user_id = user[0]
            cursor.execute("UPDATE users SET emp_number = ?, gender = ?, occupation = ? WHERE user_id = ?",
                           (emp_number, gender, occupation, user_id))

        else: 

            cursor.execute(
                "INSERT INTO users (name, emp_number, gender, occupation) VALUES (?, ?, ?, ?)",
                 (name, emp_number, gender, occupation)
            )

            conn.commit()
            user_id = cursor.lastrowid

        face_captured = False
        retries = 0
        max_retries = 5 
        capture_timeout = 10
        start_time = time.time()

        while retries < max_retries:
            ret, frame = video_capture.read()
            if not ret:
                messagebox.showerror("Camera Error",f"Attempt {retries + 1}: Failed to read from the camera. Retrying...")
                retries += 1
                continue 
                
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame, model = "hog")

            if face_locations:

                for (top, right, bottom, left) in face_locations:
                    cv2.rectangle(frame, (left, top), (right, bottom), (0,255,0), 2)
                
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                if len(face_encodings) > 0:
                    face_encoding = face_encodings[0]
                try:
                    face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
                    if self.is_face_duplicate(face_encoding):
                        messagebox.showerror("Error", "This face is already registered.")
                        break

                    encoded_face = face_encoding.tobytes()
                    cursor.execute("UPDATE users SET face_encoding = ? WHERE user_id = ?", (encoded_face, user_id))
                    conn.commit()
                    self.known_face_encodings.append(face_encoding)
                    self.load_known_faces()
                    face_captured = True
                    break
                except Exception as e:
                    messagebox.showerror("Database Error", f"Failed to register face encoding: {str(e)}")
                    break
       

            cv2.imshow("Camera - User Registration", frame)

            key = cv2.waitKey(1)

            if key == ord('q'):
                break

            attempt_counter +=1

            elapsed_time = time.time() - start_time
            if elapsed_time >= capture_timeout:
                retry = messagebox.askretrycancel("Timeout", "Face capture timed out. Please try again.")
                if retry:
                 start_time = time.time()
                 attempt_counter = 0
            
            else:
                break

        retries += 1

        video_capture.release()
        cv2.destroyAllWindows()
        
        if face_captured:
            messagebox.showinfo("Success", "Face registered successfully!")
        else:
            messagebox.showerror("Face Not Detected", "No face detected. Please try again.")
  
    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    # Function to export logs to PDF's
    def export_logs_to_pdf(self):
        file_path = filedialog.asksaveasfilename(defaultextension = ".pdf", filetypes = [("PDF files", "*.pdf")])
        if not file_path:
            return 
        
        pdf = canvas.Canvas(file_path, pagesize = letter)
        pdf.setFont("Helvetica", 12)

        cursor.execute("SELECT * FROM clock_logs")
        logs = cursor.fetchall()

        if not logs:
            pdf.drawString(100, 750, "No logs found." )
        else:
            pdf.drawString(100, 750, "Clocking Logs:")
            y_position = 730
            for log in logs:
                log_text = f"User ID: {log[1]}, Clock-In: {log[2]}, Clock-Out: {log[3]}"
                pdf.drawString(100, y_position, log_text)
                y_position -=20

                if y_position < 50:
                    pdf.showPage()
                    pdf.setFont("Helvetica", 12)
                    y_position = 750
            pdf.save()
            messagebox.showinfo("Success", "Logs exported successfully as PDF!")


        

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
        
        ctk.CTkButton(self.content_frame, text="Export Logs as PDF", command=self.export_logs_to_pdf, width=200).pack(pady=20)
        ctk.CTkButton(self.content_frame, text="Refresh Logs", command=self.show_logs, width=200).pack(pady=20)
    

if __name__ == "__main__":
    app = ClockingApp(conn)
    app.mainloop()
