import sqlite3
import customtkinter as ctk
from tkinter import messagebox
import re

# Initialize database
conn = sqlite3.connect('user_data.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        company TEXT NOT NULL
    )
''')
conn.commit()
conn.close()

# Functions to switch between frames
def switch_to_register():
    login_frame.pack_forget()
    entry_username.delete(0, 'end')
    entry_name.delete(0, 'end')
    entry_password.delete(0, 'end')
    entry_confirm_password.delete(0, 'end')
    entry_email.delete(0, 'end')
    entry_company.delete(0, 'end')
    register_frame.pack(pady=20)


# Function to switch to the login frame
def switch_to_login():
    register_frame.pack_forget() 
    login_frame.pack(pady=20, padx=20, expand=True)


# Function to handle registration

def register_user():
    username = entry_username.get()
    name = entry_name.get()
    password = entry_password.get()
    confirm_password = entry_confirm_password.get()
    email = entry_email.get()
    company = entry_company.get()

    # Validate required fields
    if not (username and name and password and confirm_password and email and company):
        messagebox.showerror("Error", "All fields are required")
        return
    
    # Check if passwords match
    if password != confirm_password:
        messagebox.showerror("Error", "Passwords do not match")
        return
    
    # Validate email format
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        messagebox.showerror("Error", "Invalid email format")
        return
    
    # Connect to the database
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    
    # Check for existing username or email
    cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
    existing_user = cursor.fetchone()
    
    if existing_user:
        if existing_user[0] == username: 
            messagebox.showerror("Error", "Username already exists")
        elif existing_user[3] == email:  
            messagebox.showerror("Error", "Email already registered")
        conn.close()
        return
    
    # Insert new user
    try:
        # Insert the new user
        cursor.execute('INSERT INTO users (username, name, password, email, company) VALUES (?, ?, ?, ?, ?)',
                       (username, name, password, email, company))
        conn.commit()
        messagebox.showinfo("Success", "Registration Successful")
        switch_to_login()  
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username or email already exists")
    finally:
        conn.close()


# Function to handle login
def login_user():
    username = login_username.get()
    password = login_password.get()
    
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    result = cursor.fetchone()  
    
    if result:
        messagebox.showinfo("Success", f"Welcome, {result[1]} from {result[3]}")
    else:
        messagebox.showerror("Error", "Invalid username or password")
    
    conn.close()

# Initialize CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Registration and Login System")

# Function to center the window
def center_window(app, width, height):
    screen_width = app.winfo_screenwidth()
    screen_height = app.winfo_screenheight()
    
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))
    
    app.geometry(f"{width}x{height}+{x}+{y}")

# Set window size and center it
window_width = 450
window_height = 500
center_window(app, window_width, window_height)

# Common Frame Settings
frame_width = 400
frame_height = 450

# Registration Frame
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

register_button = ctk.CTkButton(register_frame, text="Register", width=200, command= register_user)
register_button.pack(pady=15, padx=20)


switch_to_login_btn = ctk.CTkButton(register_frame, text="Already have an account?", width=200, command= switch_to_login)
switch_to_login_btn.pack(pady=5)

# Login Frame
login_frame = ctk.CTkFrame(app, width=frame_width, height=frame_height)

ctk.CTkLabel(login_frame, text="Login", font=("Arial", 24)).pack(pady=15)

login_username = ctk.CTkEntry(login_frame, placeholder_text="Username", width=300)
login_username.pack(pady=10, padx=20)

login_password = ctk.CTkEntry(login_frame, placeholder_text="Password", show="*", width=300)
login_password.pack(pady=10, padx=20)

login_button = ctk.CTkButton(login_frame, text="Login", width=200, command=login_user)
login_button.pack(pady=15, padx=20)

switch_to_register_btn = ctk.CTkButton(login_frame, text="Don't have an account? Register", width=200, command= switch_to_register)
switch_to_register_btn.pack(pady=5)


# Start with the registration frame visible
register_frame.pack(pady=20, padx=20, expand=True)

app.mainloop()

