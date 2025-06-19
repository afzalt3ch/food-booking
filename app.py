# app.py (Backend - Python/Flask)
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from reportlab.pdfgen import canvas
from twilio.rest import Client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from fpdf import FPDF
from data import students
from registration import *
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Global shutdown flag
shutdown_mode = False

# Database Setup
def init_db():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    
    # Create Students Table
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (id INTEGER PRIMARY KEY, 
                 name TEXT, 
                 department TEXT, 
                 dob TEXT)''')
    
    # Create Tokens Table
    c.execute('''CREATE TABLE IF NOT EXISTS tokens
                 (id INTEGER PRIMARY KEY,
                 student_id INTEGER,
                 booking_date TEXT,
                 valid_date TEXT,
                 FOREIGN KEY(student_id) REFERENCES students(id))''')

    # Create Token Archive Table
    # This table will store daily archived token data
    c.execute('''CREATE TABLE IF NOT EXISTS token_archive
                 (id INTEGER PRIMARY KEY,
                 student_id INTEGER,
                 booking_date TEXT,
                 valid_date TEXT,
                 archived_at DATE, -- The date when the token was archived
                 FOREIGN KEY(student_id) REFERENCES students(id))''')

    conn.commit()
    conn.close()

init_db()

# Helper Functions
def current_time():
    return datetime.now().strftime("%H:%M")

def is_booking_time():
    return "10:00" <= current_time() <= "23:59"

@app.route('/toggle_shutdown', methods=['POST'])
def toggle_shutdown():
    global shutdown_mode
    shutdown_mode = not shutdown_mode  # Toggle shutdown mode
    return render_template('admin.html', shutdown_mode=shutdown_mode)

# Routes
@app.route('/')
def login():
    
    return render_template('login.html')

@app.route('/auth', methods=['POST'])
def authenticate():
    global shutdown_mode
    if shutdown_mode:
        return render_template('shutdown.html')  # Prevent login if shutdown is active

    name = request.form['username']
    dob = request.form['password']
    
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute('SELECT * FROM students WHERE name=? AND dob=?', (name, dob))
    student = c.fetchone()
    conn.close()
    
    if student:
        session['user_id'] = student[0]
        session['name'] = student[1]
        session['department'] = student[2]
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', error="Invalid credentials")
from datetime import datetime, timedelta

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('students.db')
    c = conn.cursor()

    # Check if the user has already booked a token for the next day
    valid_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    c.execute('''SELECT * FROM tokens 
                 WHERE student_id=? AND valid_date=?''', 
              (session['user_id'], valid_date))
    existing_token = c.fetchone()

    # Flag to indicate if the user has already booked
    already_booked = True if existing_token else False

    # Get user's tokens
    c.execute('''SELECT * FROM tokens 
                 WHERE student_id=? 
                 ORDER BY valid_date DESC''', (session['user_id'],))
    user_tokens = c.fetchall()

    # Get all tokens
    c.execute('''SELECT students.department, students.name, tokens.valid_date 
                 FROM tokens 
                 JOIN students ON tokens.student_id = students.id''')
    all_tokens = c.fetchall()

    conn.close()

    return render_template('dashboard.html', 
                          is_booking_time=is_booking_time(),
                          user_tokens=user_tokens,
                          all_tokens=all_tokens,
                          already_booked=already_booked)


@app.route('/book', methods=['POST'])
def book_token():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if not is_booking_time():
        return redirect(url_for('dashboard'))
    
    booking_date = datetime.now().strftime("%Y-%m-%d")
    valid_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute('INSERT INTO tokens (student_id, booking_date, valid_date) VALUES (?,?,?)',
              (session['user_id'], booking_date, valid_date))
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/delete/<int:token_id>')
def delete_token(token_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute('DELETE FROM tokens WHERE id=? AND student_id=?',
              (token_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard'))

def generate_pdf():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute('''SELECT students.name, students.department, tokens.valid_date 
                 FROM tokens 
                 JOIN students ON tokens.student_id = students.id''')
    data = c.fetchall()
    conn.close()
    
    pdf = canvas.Canvas("tokens.pdf")
    y = 800
    pdf.drawString(50, y, "Booked Tokens:")
    for row in data:
        y -= 20
        pdf.drawString(50, y, f"Name: {row[0]}, Department: {row[1]}, Valid Date: {row[2]}")
    pdf.save()
    
    return len(data)

# Scheduled Task (Run daily at 1 AM)
def daily_task():
    bookings_count = generate_pdf()

    # Send Email
    msg = MIMEMultipart()
    msg['Subject'] = 'Daily Token Report'
    msg['From'] = 'afzalhakkim11b@gmail.com'
    msg['To'] = 'afzalhakkim666@gmail.com'
    
    with open("tokens.pdf", "rb") as f:
        attach = MIMEApplication(f.read(),_subtype="pdf")
    attach.add_header('Content-Disposition','attachment',filename="tokens.pdf")
    msg.attach(attach)
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()  # Secures the connection
        server.login('afzalhakkim11b@gmail.com', 'your_app_password')  # Use App Password instead of normal password for Gmail
        server.send_message(msg)

    # Send SMS using Twilio
    client = Client('your_twilio_account_sid', 'your_twilio_auth_token')
    client.messages.create(
        body=f"Total bookings today: {bookings_count}",
        from_='+7306553870',  # Your Twilio number
        to='+7994207908'  # Recipient's phone number
    )

# app.py (Backend - Python/Flask)
@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/all_data')
def all_data():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    
    # Remove duplicate rows based on name, department, and dob, keeping only one instance
    c.execute('''
        DELETE FROM students
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM students
            GROUP BY name, department, dob
        )
    ''')
    conn.commit()

    # Fetch all students data (after removing duplicates)
    c.execute('SELECT * FROM students')
    students_data = c.fetchall()
    conn.close()
    
    # Render the admin.html page with the cleaned students_data
    return render_template('admin.html', all_data=students_data, token_data=None)

@app.route('/admin_auth', methods=['POST'])
def admin_authenticate():
    # Hardcoded admin credentials
    admin_username = "admin"
    admin_password = "123"
    
    # Get input from form (if needed, can adjust form input fields for admin login)
    username = request.form.get('username', 'admin')
    password = request.form.get('password', '123')
    
    # Check if the entered credentials match the admin credentials
    if username == admin_username and password == admin_password:
        return redirect(url_for('admin_page'))
    else:
        return render_template('login.html', error="Invalid admin credentials")

@app.route('/admin_page')
def admin_page():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    
    # Correct query to select all distinct student records
    c.execute('SELECT DISTINCT id, name, department, dob FROM students')
    students = c.fetchall()
    
    conn.close()
    
    return render_template('admin.html', students=students)

# Function to send SMS
def send_sms(to_number, message_body):
    # Twilio account details
    account_sid = 'AC0ba65060d998de4316fd164ea6917263'
    auth_token = '0e3740c13cc592ea5f7bc50fc8e37d7b'
    client = Client(account_sid, auth_token)

    # Send SMS
    message = client.messages.create(
        body=message_body,
        from_='+17545475949',  # Your Twilio number
        to=to_number                      # Receiver's phone number
    )
    return message.sid

# Flask route to handle sending SMS
# Example query to get the total number of token rows
@app.route('/send_sms', methods=['POST'])
def handle_send_sms():
    phone_number = request.form['phone']
    
    # Establish a connection to the database (replace 'database.db' with your actual database)
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    
    # Query to fetch the count of token rows
    query = "SELECT COUNT(*) FROM tokens"  
    cursor.execute(query)
    token_count = cursor.fetchone()[0]
    
    # Close the cursor and connection
    cursor.close()
    conn.close()

    # SMS message body
    message_body = f"Total number of token bookings: {token_count}"
    
    # Send the SMS (assuming you have a send_sms function set up)
    send_sms(phone_number, message_body)
    
    return "SMS Sent Successfully!"

@app.route('/send_pdf_email', methods=['POST'])
def send_pdf_email():
    email = request.form['email']
    
    # Generate PDF from token data in the database
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    
    # Fetch tokens and corresponding student data
    cursor.execute('''SELECT students.name, students.department, tokens.valid_date, tokens.booking_date 
                      FROM tokens 
                      JOIN students ON tokens.student_id = students.id''')
    tokens = cursor.fetchall()
    cursor.close()
    conn.close()

    # Create a PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Token List", ln=True, align="C")
    
    # Table headers
    pdf.cell(50, 10, txt="Name", border=1)
    pdf.cell(50, 10, txt="Department", border=1)
    pdf.cell(50, 10, txt="Valid Date", border=1)
    pdf.cell(50, 10, txt="Booking Date", border=1)
    pdf.ln()

    # Populate table with actual data from the query
    for token in tokens:
        name, department, valid_date, booking_date = token
        pdf.cell(50, 10, txt=str(name), border=1)
        pdf.cell(50, 10, txt=str(department), border=1)
        pdf.cell(50, 10, txt=str(valid_date), border=1)
        pdf.cell(50, 10, txt=str(booking_date), border=1)
        pdf.ln()

    pdf_file = 'tokens_list.pdf'
    pdf.output(pdf_file)

    # Send email with PDF attached
    sender_email = "ksathira3062@gmail.com"
    sender_password = "dhym xjeh cepj ggus"
    receiver_email = email

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Token List PDF"

    body = "Please find attached the Token List PDF."
    msg.attach(MIMEText(body, 'plain'))

    # Open PDF file in binary mode
    with open(pdf_file, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f"attachment; filename= {pdf_file}",
        )
        msg.attach(part)

    # SMTP setup to send email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        return "Email sent successfully"
    except Exception as e:
        print(f"Failed to send email: {e}")
        return "Failed to send email", 500
    finally:
        # Delete the PDF file after sending
        if os.path.exists(pdf_file):
            os.remove(pdf_file)

@app.route('/register_student', methods=['POST'])
def register_student_route():
    return register_student()

@app.route('/verify_student/<int:student_id>', methods=['POST'])
def verify_student_route(student_id):
    return verify_student(student_id)

# Route to render the student registration form
@app.route('/register', methods=['GET'])
def show_registration_form():
    return render_template('register.html')  # This will render the registration page

@app.route('/admin_panel', methods=['GET'])
def admin_panel_route():
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()

    # Fetch all unverified students from the database
    cursor.execute("SELECT * FROM unverified_students")
    unverified_students = cursor.fetchall()
    
    conn.close()

    # Pass the data to the HTML template
    return render_template('admin_panel.html', unverified_students=unverified_students)

@app.route('/reject_student/<int:student_id>', methods=['POST'])
def reject_student(student_id):

    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()

    # Remove student from the unverified students table
    cursor.execute("DELETE FROM unverified_students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()

    # Redirect back to the admin panel after rejecting the student
    return redirect('/admin_panel')

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    conn = sqlite3.connect('students.db')
    cur = conn.cursor()

    try:
        cur.execute('DELETE FROM students WHERE id = ?', (student_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to delete a token by student ID
# Route to delete a token by token_id and student_id
@app.route('/remove_token/<string:student_name>', methods=['POST'])
def remove_token(student_name):
    conn = sqlite3.connect('students.db')
    cur = conn.cursor()

    try:
        # Get student_id from the students table using the student_name
        cur.execute('SELECT id FROM students WHERE name = ?', (student_name,))
        student = cur.fetchone()

        if not student:
            return jsonify({'error': 'Student not found'}), 404

        student_id = student[0]

        # Delete token where student_id matches
        cur.execute('DELETE FROM tokens WHERE student_id = ?', (student_id,))
        conn.commit()

        if cur.rowcount == 0:
            return jsonify({'error': 'No token found for this student'}), 404

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        print(f"Error while deleting token: {str(e)}")
        return jsonify({'error': str(e)}), 500

    finally:
        conn.close()

from datetime import datetime  # Correct datetime import

@app.route('/archive_tokens', methods=['POST'])
def archive_tokens():
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')  # Use correct import and method

    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    
    # Select all tokens from the `tokens` table where the `booking_date` is before today
    c.execute('''SELECT student_id, booking_date, valid_date FROM tokens WHERE booking_date < ?''', (today,))
    tokens_to_archive = c.fetchall()
    
    # Insert the selected tokens into the `token_archive` table
    for token in tokens_to_archive:
        c.execute('''INSERT INTO token_archive (student_id, booking_date, valid_date, archived_at)
                     VALUES (?, ?, ?, ?)''', (token[0], token[1], token[2], today))

    # Delete the archived tokens from the `tokens` table
    c.execute('DELETE FROM tokens WHERE booking_date < ?', (today,))
    
    conn.commit()
    conn.close()

    return "Tokens archived successfully"

# Archive tokens when needed
archive_tokens()


@app.route('/view_archived_tokens', methods=['GET', 'POST'])
def view_archived_tokens():
    if request.method == 'POST':
        selected_date = request.form['selected_date']
        conn = sqlite3.connect('students.db')
        c = conn.cursor()
        
        # Fetch archived tokens for the selected date
        c.execute('''SELECT students.name, students.department, token_archive.valid_date, token_archive.booking_date
                     FROM token_archive 
                     JOIN students ON token_archive.student_id = students.id
                     WHERE token_archive.archived_at = ?''', (selected_date,))
        archived_token_data = c.fetchall()
        conn.close()

        return render_template('admin.html', archived_token_data=archived_token_data, selected_date=selected_date)
    
    # If no date is selected, show an empty form
    return render_template('admin.html', archived_token_data=None, selected_date=None)

@app.route('/token_list')
def token_list():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()

    # Fetch students who booked tokens, selecting more fields if necessary
    c.execute('''SELECT students.name, students.department, tokens.valid_date, tokens.booking_date 
                 FROM tokens 
                 JOIN students ON tokens.student_id = students.id''')
    token_data = c.fetchall()
    conn.close()

    return render_template('admin.html', all_data=None, token_data=token_data)


if __name__ == '__main__':
    app.run(debug=True)