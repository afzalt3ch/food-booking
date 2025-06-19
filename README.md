<p align="center">
  <img src="https://raw.githubusercontent.com/afzalt3ch/banner.png/main/Gemini_Generated_Image_hb31fqhb31fqhb31.png" alt="WeeBee Banner" width="100%" />
</p>

# 🍽️ Food Token Booking Web App

A smart and student-friendly web application that allows college students to book next-day food tokens online, manage their profiles, receive daily booking stats via **email and SMS**, and maintain admin controls – all built using **Python Flask** and **SQLite**.

---

## ✨ Key Features

### 🧑‍🎓 Student Features

- 🔐 **Student Login & Registration**
  - Login using *Name + Date of Birth* (DOB).
  - Upload **BPL Certificate** during registration (image formats allowed).
  - Admin verification required to activate access.

- 📅 **Token Booking System**
  - Students can book **only 1 token per day** for **next day**.
  - Booking window: **10:00 AM to 11:59 PM**
  - View all previously booked tokens and delete if needed.
  - Built-in **countdown timer** to booking close time.

- 📸 **Upload Handling**
  - Students upload BPL certificate securely to `/static/uploads/`.

---

### 🛠️ Admin Features

- 🧾 **Admin Login & Dashboard**
  - Hardcoded admin credentials.
  - View all registered and verified students.
  - Toggle **shutdown mode** for maintenance (disables student login).
  
- ✅ **Student Verification Panel**
  - Review & verify pending student applications with BPL proofs.
  - View uploaded images and accept/reject instantly.

- 🧾 **Token Insights**
  - View all tokens booked by students.
  - Search tokens by archived date.
  - Daily tokens can be exported as a **PDF**.

- 🗑️ **Data Cleanup**
  - Remove duplicate students.
  - Delete tokens and student records on the fly.

---

### 📤 Notifications

- 📧 **Email**
  - Admin receives a PDF report with booking details.
  - Can send the token list PDF to any email.

- 📱 **SMS Alerts**
  - Admin can send total token count to a number using **Twilio SMS**.
  - Daily booking summary sent via SMS at 1 AM.

---

## 💡 Technical Stack

- **Backend**: Python, Flask
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **PDF Generation**: FPDF, ReportLab
- **Notifications**: SMTP (Gmail), Twilio SMS API

---

## 🧠 Database Tables

- `students`: Verified student data
- `unverified_students`: Pending registrations
- `tokens`: Active bookings
- `token_archive`: Archived tokens after use

---

## 🗂️ Folder Structure

```
food-token-app/
├── app.py
├── data.py
├── registration.py
├── students.db
├── static/
│   └── uploads/        # Uploaded certificates
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── admin.html
│   ├── admin_panel.html
│   └── shutdown.html
├── screenshots/
│   ├── login.png
│   ├── register.png
│   ├── admin_page.png
│   └── dashboard.png
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/afzalt3ch/food-token-booking-app.git
cd food-token-booking-app
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Flask App

```bash
python app.py
```

Visit: [http://localhost:5000](http://localhost:5000)

---

## ⚠️ Configuration Notes

- ✉️ **Gmail Setup**:
  - You must enable **"Less secure apps"** or use an **App Password**.
  - Update sender email/password in:
    ```python
    msg['From'] = 'your_email@gmail.com'
    server.login('your_email@gmail.com', 'your_app_password')
    ```

- 📲 **Twilio SMS Setup**:
  - Replace placeholder values with your Twilio credentials:
    ```python
    client = Client('your_twilio_sid', 'your_twilio_token')
    from_ = 'your_twilio_number'
    to = 'verified_number_to_receive_sms'
    ```

- 🗓️ **Scheduled Tasks**:
  - You can automate the `daily_task()` function via a cron job or background thread (e.g., with `APScheduler`).

---

## 📷 Screenshots

| Login | Register |
|-------|----------|
| ![](https://github.com/afzalt3ch/food-booking/blob/main/screenshots/login.png) | ![](https://github.com/afzalt3ch/food-booking/blob/main/screenshots/register.png) |

| Dashboard | Admin Panel |
|----------|-------------|
| ![](https://github.com/afzalt3ch/food-booking/blob/main/screenshots/dashboard.png) | ![](https://github.com/afzalt3ch/food-booking/blob/main/screenshots/admin_page.png) |

---

## 📜 License

This project is licensed under the **MIT License**.

---

<p align="center">Made with ❤️ by <strong>Afzal T3ch</strong></p>
