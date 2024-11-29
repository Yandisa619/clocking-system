import sqlite3
import tkinter
import customtkinter as ctk
from tkinter import messagebox
import re
import hashlib
from PIL import Image
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import face_recognition
import cv2
import numpy as np
import subprocess


#
# Initialize database
conn = sqlite3.connect('clocking_system.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin_info (
        username TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        company TEXT NOT NULL,
        image BLOB,
        face_encoding BLOB
    )
''')
conn.commit()
conn.close()

def send_password_recovery(email):
    sender_email = "ntombekhaya.mkaba@capaciti.org.za"
    sender_password = "Ntosh98*#"
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = email
    message['Subject'] = "Password Recovery"

    body = "Click the link below to reset your password:\n\nhttps://example.com/recover_password"
    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
        print("Password recovery email sent!")
    except Exception as e:
        print(f"Error sending email: {e}")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_temp_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def is_valid_email(email):
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(email_regex, email) is not None

def switch_to_register():
    login_frame.pack_forget()
    register_frame.pack(pady=20)
   
    # Force redraw (optional but might help)
    entry_username.update()
    entry_name.update()
    entry_email.update()
    entry_password.update()
    entry_confirm_password.update()
    entry_company.update()

def switch_to_login():
    register_frame.pack_forget()
    login_frame.pack(pady=20, padx=20, expand=True)

# Function to handle registration with face recognition
def register_user():
    username = entry_username.get()
    name = entry_name.get()
    password = entry_password.get()
    confirm_password = entry_confirm_password.get()
    email = entry_email.get()
    company = entry_company.get()

    if not (username and name and password and confirm_password and email and company):
        messagebox.showerror("Error", "All fields are required")
        return

    if password != confirm_password:
        messagebox.showerror("Error", "Passwords do not match")
        return
    
    if not is_valid_email(email):
        messagebox.showerror("Error", "Invalid email format")
        return
    
    conn = sqlite3.connect('clocking_system.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM admin_info WHERE username = ? OR email = ?', (username, email))
    existing_user = cursor.fetchone()

    if existing_user:
        messagebox.showerror("Error", "Username or Email already exists")
        conn.close()
        return
    


    
    # Capture face for registration
    messagebox.showinfo("Capture Face", "Please look at the camera to capture your face.")
    video_capture = cv2.VideoCapture(0)
    ret, frame = video_capture.read()
    if not ret:
        messagebox.showerror("Error", "Could not access the camera.")
        return

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    
    if not face_encodings:
        messagebox.showerror("Error", "No face detected. Please try again.")
        return

    face_encoding = face_encodings[0]  # Capture first face
    face_encoding_blob = np.array(face_encoding).tobytes()

    # Insert user into the database along with the face encoding
    try:
        hashed_password = hash_password(password)
        cursor.execute('INSERT INTO admin_info (username, name, password, email, company, face_encoding) VALUES (?, ?, ?, ?, ?, ?)',
                       (username, name, hashed_password, email, company, face_encoding_blob))
        conn.commit()
        messagebox.showinfo("Success", "Registration Successful")
        switch_to_login()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username or email already exists")
    finally:
        conn.close()

def login_user():
    username = login_username.get()
    password = login_password.get()

    conn = sqlite3.connect('clocking_system.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM admin_info WHERE username = ?', (username,))
    result = cursor.fetchone()
    
    if result:
        stored_password = result[3]
        if stored_password == hash_password(password):  
          
             
             messagebox.showinfo("Success", f"Welcome, {username}")

  
       
             subprocess.Popen(["python", r'C:\Users\Capaciti\Documents\GitHub\clocking-system\main.py'])          
        else:
            messagebox.showerror("Error", "Invalid password")
    else:
        messagebox.showerror("Error", "Invalid username")
    
    conn.close()


def forgot_password(event=None):
    forgot_window = ctk.CTkToplevel(app)
    forgot_window.geometry("400x200")
    forgot_window.title("Password Recovery")

    label = ctk.CTkLabel(forgot_window, text="Enter your registered email:", font=('Poppins', 14))
    label.pack(pady=20)

    email_entry = ctk.CTkEntry(forgot_window, width=300, placeholder_text="Email")
    email_entry.pack(pady=10)


    def submit_email():
        email = email_entry.get()
        if is_valid_email(email):
            print(f"Password recovery sent to {email}")
            forgot_window.destroy()
        else: 
            messagebox.showerror = ("Error", "Email is not valid" )

    submit_button = ctk.CTkButton(forgot_window, text="Submit", command=submit_email)
    submit_button.pack(pady=10)


def center_window(app, width, height):
    screen_width = app.winfo_screenwidth()
    screen_height = app.winfo_screenheight()
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))
   
    app.geometry(f"{width}x{height}+{x}+{y}")
 


    #function for face 

def authenticate_with_face():
    video_capture = cv2.VideoCapture(0)
    ret, frame = video_capture.read()
    if not ret:
        messagebox.showerror("Error", "Could not access the camera.")
        return

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    
    if not face_encodings:
        messagebox.showerror("Error", "No face detected. Please try again.")
        return

    # Compare face with stored faces in database
    conn = sqlite3.connect('clocking_system.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, face_encoding FROM admin_info')
    users = cursor.fetchall()

    for username, stored_face_encoding in users:
        stored_face_encoding = np.frombuffer(stored_face_encoding, dtype=np.float64)
        matches = face_recognition.compare_faces([stored_face_encoding], face_encodings[0], tolerance=0.5)

        if True in matches:
            messagebox.showinfo("Success", f"Welcome, {username}")
            
            subprocess.Popen(["python", r'C:\Users\Capaciti\Documents\GitHub\clocking-system\main.py'])          
           
            conn.close()
            return
    
    messagebox.showerror("Error", "Face not recognized.")
    conn.close()

# Initialize CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Registration and Login System")

# Set window size and center it
window_width = 400
window_height = 500
center_window(app, window_width, window_height)
 
# screen_width = app.winfo_screenwidth()
# screen_height = app.winfo_screenheight()
 
# bg_image = ctk.CTkImage(
#     light_image=Image.open("pexels-googledeepmind-18069161.jpg"),
#     dark_image=Image.open("pexels-googledeepmind-18069161.jpg"),
#     size=(screen_width, screen_height)
# )

# bg_label = ctk.CTkLabel(app, image=bg_image, text="")
# bg_label.place(x=0, y=0, relwidth=1, relheight=1)


# Common Frame Settings
frame_width = 400
frame_height = 450

# Registration Frame
register_frame = ctk.CTkFrame(app, width=frame_width, height=frame_height)
register_frame.pack_propagate(False)
 
register_frame = ctk.CTkFrame(app, width=frame_width, height=frame_height)
register_frame.pack(pady=20, padx=20, expand=True)

ctk.CTkLabel(register_frame, text="Register", font=("Arial", 24)).pack(pady=15)

entry_username = ctk.CTkEntry(register_frame, placeholder_text="Username", width=300)
entry_username.pack(pady=10, padx=20)

entry_name = ctk.CTkEntry(register_frame, placeholder_text="Name", width=300)
entry_name.pack(pady=10, padx=20)

entry_email = ctk.CTkEntry(register_frame, placeholder_text="Email", width=300)
entry_email.pack(pady=10, padx=20)

entry_password = ctk.CTkEntry(register_frame, placeholder_text="Password", show="*", width=300)
entry_password.pack(pady=10, padx=20)

entry_confirm_password = ctk.CTkEntry(register_frame, placeholder_text="Confirm Password", show="*", width=300)
entry_confirm_password.pack(pady=10, padx=20)

entry_company = ctk.CTkEntry(register_frame, placeholder_text="Company", width=300)
entry_company.pack(pady=10, padx=20)

# Capture Face Button
capture_face_button = ctk.CTkButton(register_frame, text="Capture Face", width=200, command=register_user)
capture_face_button.pack(pady=15, padx=20)

register_button = ctk.CTkButton(register_frame, text="Register", width=200, command=register_user)
register_button.pack(pady=10, padx=20)

switch_to_login_btn = ctk.CTkButton(register_frame, text="Already have an account?", width=200, command=switch_to_login)
switch_to_login_btn.pack(pady=(5, 20), padx=20) 
# Login Frame
login_frame = ctk.CTkFrame(app, width=frame_width, height=frame_height)
login_frame.pack_propagate(False)
 
login_frame = ctk.CTkFrame(app, width=frame_width, height=frame_height)

ctk.CTkLabel(login_frame, text="Login", font=("Arial", 24)).pack(pady=15)

login_username = ctk.CTkEntry(login_frame, placeholder_text="Username", width=300)
login_username.pack(pady=10, padx=20)

login_password = ctk.CTkEntry(login_frame, placeholder_text="Password", show="*", width=300)
login_password.pack(pady=10, padx=20)

login_button = ctk.CTkButton(login_frame, text="Login", width=200, command=login_user)
login_button.pack(pady=15, padx=20)

# Face Recognition Login Button
face_recognition_button = ctk.CTkButton(login_frame, text="Login with Face Recognition", width=200, command=authenticate_with_face)
face_recognition_button.pack(pady=10)


account_label = ctk.CTkLabel(
    login_frame,
    text="Don't have an account? Register",
    text_color="grey",  
    cursor="hand2",  
    font=("Arial", 14)  
)


account_label.bind("<Button-1>", lambda e:switch_to_register())
account_label.pack(pady=5)


forgot_password_label = ctk.CTkLabel(
    login_frame,
    text="Forgot Password?",
    text_color="grey", 
    cursor="hand2", 
    font=("Arial", 14 ) 
)

# Bind click event to the label
forgot_password_label.bind("<Button-1>", lambda e: forgot_password())
forgot_password_label.pack(pady=5)

# Start with the registration frame visible
register_frame.pack(pady=20, padx=20, expand=True)

app.mainloop()

