# This version uses Flask + MySQL
# Install dependencies:
# pip install flask flask-mysqldb flask-login flask-wtf wtforms

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, abort
from flask_mysqldb import MySQL
from io import BytesIO
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from wtforms import Form, StringField, PasswordField, validators, TextAreaField, SubmitField, TextAreaField
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm
from datetime import datetime
import MySQLdb.cursors



app = Flask(__name__)
app.secret_key = 'dont tell anyone'

# MySQL config
app.config['MYSQL_HOST'] = 'localhost' #Change according to your host
app.config['MYSQL_USER'] = 'Admin' #Change according to your username
app.config['MYSQL_PASSWORD'] = 'Admin' #Change according to your password
app.config['MYSQL_DB'] = 'Bored_Games'

mysql = MySQL(app)
login_manager = LoginManager(app)

# User class
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT user_id, username, is_admin FROM user_info WHERE user_id = %s", (user_id,))

    data = cur.fetchone()
    cur.close()
    if data:
        return User(id=data[0], username=data[1], role='admin' if data[2] else 'user')
    return None

# Forms
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AddGameForm(FlaskForm):
    name = StringField('Game Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('Add Game')



@app.route('/')
def home():
    cur = mysql.connection.cursor()
    cur.execute("SELECT game_id, name, image FROM Recent_Games")
    rows = cur.fetchall()
    # Format the image field as either a URL or a flag for BLOB image
    recent_games = []
    for row in rows:
        game_id, name, image = row
        if isinstance(image, str) and image.startswith('http'):
            image_path = image  # External image URL
        else:
            image_path = "blob"  # Will be handled by /game_image/<id>
        recent_games.append((game_id, name, image_path))

    cur.execute("SELECT * FROM Upcoming_Events")
    events = cur.fetchall()
    cur.close()
    return render_template('home.html', recent_games=recent_games, events=events)

@app.route('/game/<int:game_id>')
def game_page(game_id):
    cur = mysql.connection.cursor()

    # Fetch game info
    cur.execute("SELECT * FROM Game_Details WHERE game_id = %s", (game_id,))
    game = cur.fetchone()

    if not game:
        return "Game not found", 404

    # Fetch genres
    cur.execute("SELECT genre_name FROM Game_Genres WHERE game_id = %s", (game_id,))
    genres = [row[0] for row in cur.fetchall()]

    # Fetch user's rating if logged in
    user_rating = None
    if current_user.is_authenticated:
        cur.execute("""
            SELECT Stars FROM Game_Ratings
            WHERE user_id = %s AND game_id = %s
        """, (current_user.id, game_id))
        rating_result = cur.fetchone()
        user_rating = rating_result[0] if rating_result else None

    # After user_rating section in game_page()
    cur.execute("""
        SELECT username, stars, comment
        FROM game_ratings_view
        WHERE game_id = %s
        ORDER BY stars DESC
    """, (game_id,))
    ratings = [{'username': row[0], 'stars': row[1], 'comment': row[2]} for row in cur.fetchall()]

    cur.close()

    return render_template("game.html", game=game, genres=genres, user_rating=user_rating, game_id=game_id, ratings=ratings)


@app.route('/game_image/<int:game_id>')
def serve_image(game_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT image FROM BOARD_GAMES WHERE game_id = %s", (game_id,))
    result = cur.fetchone()
    cur.close()

    if result and result[0]:
        return send_file(BytesIO(result[0]), mimetype='image/jpeg')
    return '', 404

@app.route('/events/<int:event_id>', methods=['GET', 'POST'])
def event_detail(event_id):
    cur = mysql.connection.cursor()

    # Get event and venue details
    cur.execute("""
        SELECT name, description, event_time, max_participants, nb_participant, 
            venue_name, venue_address, venue_capacity
        FROM event_details_view
        WHERE event_id = %s
    """, (event_id,))
    event = cur.fetchone()

    if not event:
        cur.close()
        return "Event not found", 404

    user_id = current_user.get_id() if current_user.is_authenticated else None

    # Check if the user is already enrolled
    is_enrolled = False
    if user_id:
        cur.execute("""
            SELECT 1 FROM ParticipateTo WHERE event_id = %s AND user_id = %s
        """, (event_id, user_id))
        is_enrolled = cur.fetchone() is not None

    cur.close()
    return render_template('event.html', event=event, event_id=event_id, is_enrolled=is_enrolled)

@app.route('/events/<int:event_id>/enroll', methods=['POST'])
@login_required
def enroll_event(event_id):
    user_id = current_user.get_id()
    cur = mysql.connection.cursor()

    # Check if already enrolled
    cur.execute("SELECT 1 FROM ParticipateTo WHERE event_id = %s AND user_id = %s", (event_id, user_id))
    if cur.fetchone():
        flash("You are already enrolled in this event.")
        cur.close()
        return redirect(url_for('event_detail', event_id=event_id))

    # Enroll the user
    try:
        cur.execute("INSERT INTO ParticipateTo (event_id, user_id) VALUES (%s, %s)", (event_id, user_id))
        cur.execute("UPDATE EVENTS SET nb_participant = nb_participant + 1 WHERE event_id = %s", (event_id,))
        mysql.connection.commit()
        flash("Successfully enrolled!")
    except Exception as e:
        mysql.connection.rollback()
        flash("Enrollment failed.")
        print(f"Error: {e}")
    finally:
        cur.close()

    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/admin/events/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))

    cur = mysql.connection.cursor()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        max_participants = request.form['max_participants']
        event_time = request.form['event_time']
        venue_id = request.form['venue_id']

        cur.execute("""
            UPDATE EVENTS
            SET name=%s, description=%s, max_participants=%s, event_time=%s, venue_id=%s
            WHERE event_id=%s
        """, (name, description, max_participants, event_time, venue_id, event_id))
        mysql.connection.commit()
        cur.close()
        flash('Event updated successfully', 'success')
        return redirect(url_for('admin_events'))

    # GET request: show form
    cur.execute("SELECT * FROM EVENTS WHERE event_id = %s", (event_id,))
    event = cur.fetchone()
    cur.execute("SELECT * FROM VENUE")
    venues = cur.fetchall()
    cur.close()
    return render_template('Admin/edit_event.html', event=event, venues=venues)


@app.route('/admin/games/add', methods=['GET', 'POST'])
@login_required
def add_game():
    if current_user.role != 'admin':
        abort(403)

    if request.method == 'POST':
        name = request.form['name']
        image = request.form['image']
        description = request.form['description']
        year_published = request.form['year_published']
        min_players = request.form['min_players']
        max_players = request.form['max_players']
        min_playtime = request.form['min_playtime']
        max_playtime = request.form['max_playtime']
        min_age = request.form['min_age']
        publisher = request.form['publisher']
        average_rating = request.form['average_rating']

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO BOARD_GAMES (name, image, description, year_published, min_players, max_players,
                                      min_playtime, max_playtime, min_age, publisher, average_rating)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, image, description, year_published, min_players, max_players,
              min_playtime, max_playtime, min_age, publisher, average_rating))
        mysql.connection.commit()
        cur.close()

        flash('Game added successfully!')
        return redirect(url_for('admin_games'))

    return render_template('Admin/add_game.html')





@app.route('/search_games')
def search_games():
    page = request.args.get('page', 1, type=int)
    per_page = 30
    offset = (page - 1) * per_page

    # Collect filter parameters
    name = request.args.get('name')
    year = request.args.get('year')
    publisher = request.args.get('publisher')
    min_age = request.args.get('min_age')
    rating = request.args.get('rating')
    genre = request.args.get('genre')

    base_query = """
        FROM BOARD_GAMES BG
        LEFT JOIN IsOfGenre IG ON BG.game_id = IG.game_id
        LEFT JOIN GENRES G ON IG.genre_id = G.genre_id
        WHERE 1=1
    """
    filters = []
    values = []

    if name:
        filters.append(" AND BG.name LIKE %s")
        values.append(f"%{name}%")
    if year:
        filters.append(" AND BG.year_published = %s")
        values.append(year)
    if publisher:
        filters.append(" AND BG.publisher LIKE %s")
        values.append(f"%{publisher}%")
    if min_age:
        filters.append(" AND BG.min_age >= %s")
        values.append(min_age)
    if rating:
        filters.append(" AND BG.average_rating >= %s")
        values.append(rating)
    if genre:
        filters.append(" AND G.name = %s")
        values.append(genre)

    filter_sql = ''.join(filters)

    # Query with LIMIT
    query = f"SELECT DISTINCT BG.game_id, BG.name, BG.image {base_query} {filter_sql} LIMIT %s OFFSET %s"
    paged_values = values + [per_page, offset]

    cur = mysql.connection.cursor()
    cur.execute(query, paged_values)
    games = cur.fetchall()

    # Count total results for pagination
    count_query = f"SELECT COUNT(DISTINCT BG.game_id) {base_query} {filter_sql}"
    cur.execute(count_query, values)
    total_games = cur.fetchone()[0]
    cur.close()

    total_pages = (total_games + per_page - 1) // per_page

    return render_template("search_games.html", games=games, page=page, total_pages=total_pages)




@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        hashed_password = generate_password_hash(password)

        cur = mysql.connection.cursor()
        try:
            # Check if username already exists
            cur.execute("SELECT * FROM Users WHERE username = %s", (username,))
            existing_user = cur.fetchone()

            if existing_user:
                flash("Username already exists", "warning")
                return render_template("register.html", form=form)

            # Insert new user
            cur.execute(
                "INSERT INTO Users (username, password, is_admin, is_blocked) VALUES (%s, %s, %s, %s)",
                (username, hashed_password, False, False)
            )
            mysql.connection.commit()
            flash("Registration successful. You can now log in.", "success")
            return redirect(url_for('login'))

        except Exception as e:
            flash(f"Database error: {e}", "danger")
        finally:
            cur.close()

    return render_template('register.html', form=form)



@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data

        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "SELECT user_id, username, password, is_admin, is_blocked FROM Users WHERE username = %s",
                (username,)
            )
            data = cur.fetchone()
        except Exception as e:
            flash('Database error: ' + str(e), 'danger')
            return render_template('login.html', form=form)
        finally:
            cur.close()

        if data:
            stored_hashed_password = data[2]
            is_blocked = data[4]  # 5th column is is_blocked

            if is_blocked:
                flash('Your account has been blocked. Please contact support.', 'danger')
                return render_template('login.html', form=form)
            
            if check_password_hash(stored_hashed_password, password):
                role = 'admin' if data[3] else 'user'
                user = User(id=data[0], username=data[1], role=role)
                login_user(user)
                flash('Login successful', 'success')

                # Redirect based on role
                if role == 'admin':
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('profile'))
            else:
                flash('Incorrect password', 'danger')
        else:
            flash('Username not found', 'danger')

    return render_template('login.html', form=form)


@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    return render_template('/Admin/admin.html', user=current_user)

# @app.route('/profile')
# @login_required
# def profile():
#     return render_template('profile.html', user=current_user)



@app.route('/block_user/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    cur = mysql.connection.cursor()
    cur.execute("UPDATE Users SET is_blocked = 1 WHERE user_id = %s", (user_id,))
    mysql.connection.commit()
    cur.close()
    flash('User blocked.')
    return redirect(url_for('admin_panel'))


@app.route('/admin/games/edit/<int:game_id>', methods=['GET', 'POST'])
@login_required
def edit_game(game_id):
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # DictCursor here too

    if request.method == 'POST':
        name = request.form['name']
        image = request.form['image']
        description = request.form['description']
        year_published = request.form['year_published']
        min_players = request.form['min_players']
        max_players = request.form['max_players']
        min_playtime = request.form['min_playtime']
        max_playtime = request.form['max_playtime']
        min_age = request.form['min_age']
        publisher = request.form['publisher']
        average_rating = request.form['average_rating']
        updated_at = datetime.now()

        cur.execute("""
            UPDATE BOARD_GAMES
            SET name=%s, image=%s, description=%s, year_published=%s,
                min_players=%s, max_players=%s, min_playtime=%s,
                max_playtime=%s, min_age=%s, publisher=%s,
                average_rating=%s, updated_at=%s
            WHERE game_id=%s
        """, (
            name, image, description, year_published, min_players, max_players,
            min_playtime, max_playtime, min_age, publisher, average_rating, updated_at, game_id
        ))

        mysql.connection.commit()
        cur.close()
        flash('Game updated successfully', 'success')
        return redirect(url_for('admin_games'))

    # GET: Show the edit form
    cur.execute("SELECT * FROM BOARD_GAMES WHERE game_id = %s", (game_id,))
    game = cur.fetchone()
    cur.close()
    return render_template('Admin/edit_game.html', game=game)


@app.route('/profile')
@login_required
def profile():
    if current_user.role == 'admin':
        abort(403)  # Forbidden
    user_id = current_user.id  # Flask-Login provides this

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Owned games
    cur.execute("""
        SELECT B.game_id, B.name, B.image, G.since
        FROM GameOwned G
        JOIN BOARD_GAMES B ON G.game_id = B.game_id
        WHERE G.user_id = %s
    """, (user_id,))
    owned_games = cur.fetchall()

    # Wishlist
    cur.execute("""
        SELECT B.game_id, B.name, B.image
        FROM WishList W
        JOIN BOARD_GAMES B ON W.game_id = B.game_id
        WHERE W.user_id = %s
    """, (user_id,))
    wishlist = cur.fetchall()

    # Ratings
    cur.execute("""
        SELECT B.name, R.Stars, R.comment
        FROM Rating R
        JOIN BOARD_GAMES B ON R.game_id = B.game_id
        WHERE R.user_id = %s
    """, (user_id,))
    ratings = cur.fetchall()

    # Events
    cur.execute("""
        SELECT E.name, E.description, E.event_time, V.name AS venue_name
        FROM ParticipateTo P
        JOIN EVENTS E ON P.event_id = E.event_id
        JOIN VENUE V ON E.venue_id = V.venue_id
        WHERE P.user_id = %s
    """, (user_id,))
    events = cur.fetchall()

    cur.close()

    return render_template('profile.html',
                           user=current_user,  # You can still access current_user.username
                           owned_games=owned_games,
                           wishlist=wishlist,
                           ratings=ratings,
                           events=events)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    return f"""
    <html>
        <head><title>Dashboard</title></head>
        <body>
            <h1>Welcome to the Dashboard</h1>
            <p>Hello, {current_user.username}!</p>
        </body>
    </html>
    """


@app.route('/admin')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    return render_template('Admin/admin.html')


@app.route('/admin/games')
@login_required
def admin_games():
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # DictCursor here
    cur.execute("SELECT game_id, name, year_published, publisher FROM BOARD_GAMES")
    games = cur.fetchall()  # Now games is a list of dictionaries
    cur.close()

    return render_template('Admin/games.html', games=games)


@app.route('/admin/events')
@login_required
def admin_events():
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT E.*, V.name AS venue_name FROM EVENTS E JOIN VENUE V ON E.venue_id = V.venue_id")
    events = cur.fetchall()
    cur.close()
    return render_template('Admin/events.html', events=events)


@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT user_id, username, is_blocked FROM Users WHERE is_admin = 0")
    users = cur.fetchall()
    cur.close()
    return render_template('Admin/users.html', users=users)


@app.route('/admin/users/<int:user_id>/toggle_block', methods=['POST'])
@login_required
def toggle_block_user(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT is_blocked FROM Users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()

    if user:
        new_status = not user[0]
        cur.execute("UPDATE Users SET is_blocked = %s WHERE user_id = %s", (new_status, user_id))
        mysql.connection.commit()
        flash('User status updated.', 'success')
    else:
        flash('User not found.', 'danger')

    cur.close()
    return redirect(url_for('admin_users'))

# @app.route('/add_game', methods=['GET', 'POST'])
# @login_required
# def add_game():
#     if current_user.role != 'admin':
#         return redirect(url_for('home'))
#     form = AddGameForm(request.form)
#     if request.method == 'POST' and form.validate():
#         cur = mysql.connection.cursor()
#         cur.execute("INSERT INTO BOARD_GAMES (name, publisher, min_players, max_players, updated_at, average_rating) VALUES (%s, %s, 2, 4, NOW(), 0.0)",
#                     (form.title.data, form.genre.data))
#         mysql.connection.commit()
#         cur.close()
#         flash('Game added successfully')
#         return redirect(url_for('admin_panel'))
#     return render_template('add_game.html', form=form)

@app.route('/wishlist/<int:game_id>', methods=['POST'])
@login_required
def add_to_wishlist(game_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("INSERT IGNORE INTO WishList (game_id, user_id) VALUES (%s, %s)", (game_id, current_user.id))
        mysql.connection.commit()
    finally:
        cur.close()
    return redirect(url_for('game_page', game_id=game_id))


@app.route('/owned/<int:game_id>', methods=['POST'])
@login_required
def add_to_owned(game_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("INSERT IGNORE INTO GameOwned (game_id, user_id, since) VALUES (%s, %s, CURDATE())", (game_id, current_user.id))
        mysql.connection.commit()
    finally:
        cur.close()
    return redirect(url_for('game_page', game_id=game_id))



# @app.route('/events')
# def events():
#     # Fetch all events and venues from DB
#     events = get_all_events()  # implement this function to get events from DB
#     return render_template('events.html', events=events)

# @app.route('/add_event', methods=['GET', 'POST'])
# def add_event():
#     venues = get_all_venues()  # fetch venues for dropdown
#     if request.method == 'POST':
#         # Read form data
#         name = request.form['name']
#         description = request.form['description']
#         event_time = request.form['event_time']
#         max_participants = int(request.form['max_participants'])
#         venue_id = int(request.form['venue_id'])

#         # Save new event to DB (implement this function)
#         add_event_to_db(name, description, event_time, max_participants, venue_id)

#         flash('Event added successfully!')
#         return redirect(url_for('events'))

#     return render_template('add_event.html', venues=venues)

# @app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
# def edit_event(event_id):
#     venues = get_all_venues()
#     event = get_event_by_id(event_id)  # Fetch event tuple/list from DB

#     if request.method == 'POST':
#         # Update event in DB
#         name = request.form['name']
#         description = request.form['description']
#         event_time = request.form['event_time']
#         max_participants = int(request.form['max_participants'])
#         venue_id = int(request.form['venue_id'])

#         update_event_in_db(event_id, name, description, event_time, max_participants, venue_id)

#         flash('Event updated successfully!')
#         return redirect(url_for('events'))

#     return render_template('edit_event.html', event=event, venues=venues)

@app.route('/admin/events/add', methods=['GET', 'POST'])
@login_required
def add_event():
    if current_user.role != 'admin':
        abort(403)  # forbid non-admins

    cur = mysql.connection.cursor()

    # Get venues for the dropdown (on GET)
    cur.execute('SELECT venue_id, name FROM VENUE')
    venues = cur.fetchall()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        event_time = request.form['event_time']  # format: 'YYYY-MM-DDTHH:MM'
        max_participants = int(request.form['max_participants'])
        venue_id = int(request.form['venue_id'])

        # nb_participant = 0 on new event
        cur.execute('''
            INSERT INTO EVENTS (name, description, max_participants, nb_participant, event_time, venue_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (name, description, max_participants, 0, event_time.replace('T', ' '), venue_id))

        mysql.connection.commit()
        cur.close()

        flash('Event added successfully!')
        return redirect(url_for('events'))

    cur.close()
    return render_template('Admin/add_event.html', venues=venues)



@app.route('/rate/<int:game_id>', methods=['POST'])
@login_required
def rate_game(game_id):
    rating = int(request.form['rating'])
    comment = request.form.get('comment', '').strip()

    if not (1 <= rating <= 5):
        return "Invalid rating value", 400

    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            INSERT INTO Rating (user_id, game_id, Stars, comment)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE Stars = %s, comment = %s
        """, (current_user.id, game_id, rating, comment, rating, comment))
        mysql.connection.commit()
    finally:
        cur.close()

    return redirect(url_for('game_page', game_id=game_id))

if __name__ == '__main__':
    app.run(debug=True)




