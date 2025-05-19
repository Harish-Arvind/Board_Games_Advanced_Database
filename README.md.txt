# 🎲 Bored Game Library Web Application

A full-stack web application to manage and explore a board game library, built with **Python (Flask)**, **MySQL**, and **HTML/CSS**.

---

## 📁 Project Structure

```
.
├── Database/
│   ├── Creation.sql
│   ├── SQL_insert_blob.txt
│   └── Views_Triggers_functions.sql
├── Dataset/ (not added for now)
│   ├── details.csv
│   └── ratings.csv
├── Webserver/
│   ├── app.py
│   ├── requirements.txt
│   ├── setup_and_run.py
│   ├── db.py
│   ├── routes.py
│   ├── forms.py
│   ├── static/
│   │   └── style.css
│   └── templates/
│       ├── base.html
│       ├── home.html
│       ├── login.html
│       ├── register.html
│       ├── dashboard.html
│       ├── admin.html
│       ├── add_game.html
│       ├── search_results.html
│       └── (Optional: game.html, event.html)
```

---

## 🚀 Features

- Visitor view: browse games and events
- User login and dashboard: rate, wish, own games and enroll for events 
- Admin panel: manage games, events, and users
- All logic handled via SQL views, triggers, and stored procedures
- WTForms-based authentication forms
- Styled using custom CSS

---

## ✅ Requirements

- Python 3.8+
- MySQL Server (e.g., MySQL Workbench or CLI)
- pip (Python package installer)

Install dependencies:

```bash
pip install -r Webserver/requirements.txt
```

---

## 🛠️ Configuration

Ensure your MySQL database credentials are correctly set in:

### 📄 `Webserver/app.py` and `Webserver/db.py`

```python
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'Admin'
app.config['MYSQL_PASSWORD'] = 'Admin'
app.config['MYSQL_DB'] = 'Bored_games'
```

> Replace with your actual DB credentials if needed (used in app.py and setup_and_run.py).

---

## 🧱 Initial Setup

1. **Create the Database**:

   Open MySQL Workbench or terminal and run the following files in order:

   - `Database/Creation.sql` – Creates tables
   - `SQL_insert_blob.txt` – Insert game data or images
   - `Database/Views_Triggers_functions.sql` – Adds views, triggers, and stored procedures
   

2. **Run the Setup Script**:

```bash
cd Webserver
python setup_and_run.py
```


---

## 🌐 Running the Application


Open your browser and go to:

```
http://localhost:5000/
```

---

## 🔐 Default Accounts (for testing)

Changes needed to be done in insertion.sql file

| Role   | Username | Password |
|--------|----------|----------|
| Admin  | Admin1   | Admin1   |
| User   | user2-21 | Admin2   |

> Credentials are checked using SQL stored procedures in `Views_Triggers_functions.sql`.

---

## 📌 Notes

- Do **not** write SQL queries in Python; use **stored procedures and views** only.
- SQL logic is isolated in `Views_Triggers_functions.sql` for better maintainability.
- Ensure the MySQL server is **running** before launching the app.

---

## 📬 Contact

For improvements, suggestions, or bugs, feel free to open an issue or send a message.

---

**Enjoy your Bored Game Library! 🎉**