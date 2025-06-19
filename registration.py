import os
import sqlite3
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Upload folder for BPL certificates
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed extensions for file uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Check if the uploaded file has a valid extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Create tables if they don't exist
def create_tables():
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()

    # Create the unverified_students table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS unverified_students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        dob TEXT NOT NULL,
        bpl_certificate TEXT NOT NULL
    )
    ''')

    # Create the verified students table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        dob TEXT NOT NULL
    )
    ''')

    conn.commit()
    conn.close()

# Call the create_tables function to create tables when the app starts
create_tables()

# Route for student registration form submission
@app.route('/register_student', methods=['POST'])
def register_student():
    # Get form data from the registration form
    name = request.form['name'].replace(" ", "_").lower()  # Convert spaces to underscores and lowercase
    department = request.form['department']
    dob = request.form['dob']
    
    # Handle BPL certificate file upload
    bpl_certificate = request.files['bpl_certificate']

    if bpl_certificate and allowed_file(bpl_certificate.filename):
        # Get the file extension
        file_ext = bpl_certificate.filename.rsplit('.', 1)[1].lower()

        # Create a new filename based on the student's name
        new_filename = f"{name}_bpl.{file_ext}"

        # Save the file to the upload folder
        cert_filename = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(new_filename))
        bpl_certificate.save(cert_filename)

        # Insert the student details into the unverified_students table
        conn = sqlite3.connect('students.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO unverified_students (name, department, dob, bpl_certificate) 
            VALUES (?, ?, ?, ?)
        ''', (name, department, dob, new_filename))
        conn.commit()
        conn.close()

        return "Registration successful! Awaiting admin verification."
    else:
        return "Invalid file format. Please upload a valid image."

# Serve the uploaded BPL certificate files
@app.route('/uploads/<filename>')
def uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Route to display the admin panel
@app.route('/admin_panel')
def admin_panel():
    # Fetch all unverified students from the database
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM unverified_students")
    unverified_students = cursor.fetchall()
    conn.close()

    # Render the admin panel page with unverified students list
    return render_template('admin_panel.html', unverified_students=unverified_students)

# Route to verify a student and move them to the main students table
def verify_student(student_id):
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()

    # Fetch the unverified student's data
    cursor.execute("SELECT * FROM unverified_students WHERE id=?", (student_id,))
    student = cursor.fetchone()

    if student:
        # Insert the student into the students (verified) table
        cursor.execute('''
            INSERT INTO students (name, department, dob) 
            VALUES (?, ?, ?)
        ''', (student[1], student[2], student[3]))

        # Delete the student from the unverified_students table
        cursor.execute("DELETE FROM unverified_students WHERE id=?", (student_id,))
        conn.commit()

    conn.close()

    # Redirect back to the admin panel after verification
    return redirect('/admin_panel')

if __name__ == '__main__':
    app.run(debug=True)
