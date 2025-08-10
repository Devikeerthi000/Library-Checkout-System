from flask import Flask, flash, render_template, request, redirect, url_for, session
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'your_secret_key'

# Function to connect to the database
def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='librarydb',
            user='root',
            password='Lally@034'
        )
        if connection.is_connected():
            print("Successfully connected to the database")
            return connection
    except Error as e:
        print(f"Database connection error: {e}")
    return None

# Function to close the database connection
def close_connection(connection):
    if connection and connection.is_connected():
        connection.close()
        print("Database connection closed")

# Home page route
@app.route('/')
def index():
    if 'user_id' not in session and 'admin_id' not in session:
        return redirect(url_for('choose_role'))  # Redirect to choose role if not logged in

    if 'user_id' in session:
        return redirect(url_for('user_dashboard'))
    elif 'admin_id' in session:
        return redirect(url_for('admin_dashboard'))

    return redirect(url_for('choose_role'))

# Choose role page route (User or Admin)
@app.route('/choose_role', methods=['GET', 'POST'])
def choose_role():
    if request.method == 'POST':
        role = request.form['role']
        if role == 'user':
            return redirect(url_for('login'))  # Redirect to user login
        elif role == 'admin':
            return redirect(url_for('admin_login'))  # Redirect to admin login
    return render_template('choose_role.html')

# User login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = connect_to_database()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            close_connection(connection)

            if user:
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                return redirect(url_for('user_dashboard'))
            else:
                return "Invalid username or password"
    return render_template('login.html')

# Admin login route
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = connect_to_database()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM admin_users WHERE username = %s AND password = %s", (username, password))
            admin = cursor.fetchone()
            close_connection(connection)

            if admin:
                session['admin_id'] = admin['admin_id']
                session['admin_username'] = admin['username']
                return redirect(url_for('admin_dashboard'))
            else:
                return "Invalid username or password"
    return render_template('admin_login.html')

# User Dashboard Route
@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' in session:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM books")
            books = cursor.fetchall()
            close_connection(connection)
            return render_template('user_dashboard.html', books=books)
        return "Unable to connect to the database"
    return redirect(url_for('login'))

# Admin Dashboard Route
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' in session:
        return render_template('admin_dashboard.html')
    return redirect(url_for('admin_login'))

def log_admin_action(admin_id, action):
    """
    Logs an admin action into the admin_logs table.
    """
    connection = connect_to_database()
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO admin_logs (admin_id, action) VALUES (%s, %s)",
            (admin_id, action)
        )
        connection.commit()
        close_connection(connection)

# Admin remove book route
@app.route('/remove_book/<int:book_id>', methods=['POST'])
def remove_book(book_id):
    if 'admin_id' in session:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM books WHERE book_id = %s", (book_id,))
            connection.commit()
            log_admin_action(session['admin_id'], "Removed Book")
            close_connection(connection)
            flash("Book removed successfully!")
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))

# User profile page route
@app.route('/users')
def users():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = connect_to_database()
    if connection:
        cursor = connection.cursor(dictionary=True)
        user_id = session['user_id']

        # Fetch user details
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user_data = cursor.fetchone()

        # Fetch user checkouts
        cursor.execute(""" 
            SELECT c.checkout_id, b.title AS book_title, cat.name AS category_name, 
                   c.checkout_date, c.return_date
            FROM checkouts c
            JOIN books b ON c.books_id = b.books_id
            JOIN book_categories bc ON b.books_id = bc.books_id
            JOIN categories cat ON bc.categories_id = cat.categories_id
            WHERE c.user_id = %s
        """, (user_id,))
        checkouts = cursor.fetchall()

        # Fetch fines
        cursor.execute(""" 
            SELECT f.fine_id, f.fine_amount, f.paid, c.checkout_id 
            FROM fines f
            JOIN checkouts c ON f.checkout_id = c.checkout_id
            WHERE c.user_id = %s
        """, (user_id,))
        fines_data = cursor.fetchall()

        close_connection(connection)
        return render_template('users.html', user=user_data, checkouts=checkouts, fines=fines_data)
    return "Unable to connect to the database"

# Books page route
@app.route('/books', methods=['GET', 'POST'])
def books():
    connection = connect_to_database()
    if connection:
        cursor = connection.cursor(dictionary=True)
        
        # Get the search query from the form
        query = request.args.get('query', '')  # Default to an empty string if no query is provided
        
        if query:
            # Search for books by title, author, or category
            sql = """
                SELECT b.*, cat.name AS category
                FROM books b
                LEFT JOIN book_categories bc ON b.books_id = bc.books_id
                LEFT JOIN categories cat ON bc.categories_id = cat.categories_id
                WHERE b.title LIKE %s OR b.author LIKE %s OR cat.name LIKE %s
            """
            like_query = f"%{query}%"
            cursor.execute(sql, (like_query, like_query, like_query))
        else:
            # If no search query, fetch all books
            cursor.execute(""" 
                SELECT b.*, cat.name AS category
                FROM books b
                LEFT JOIN book_categories bc ON b.books_id = bc.books_id
                LEFT JOIN categories cat ON bc.categories_id = cat.categories_id
            """)

        books = cursor.fetchall()

        # Convert availability to "Available" / "Not Available"
        for book in books:
            book['availability'] = 'Available' if book['availability'] == 1 else 'Not Available'

        close_connection(connection)
        return render_template('books.html', books=books, query=query)
    return "Unable to connect to the database"

# Search route
@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        query = request.form['query']
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor(dictionary=True)
            sql = """
                SELECT b.*, cat.name AS category
                FROM books b
                JOIN book_categories bc ON b.books_id = bc.books_id
                JOIN categories cat ON bc.categories_id = cat.categories_id
                WHERE b.title LIKE %s OR b.author LIKE %s OR cat.name LIKE %s
            """
            like_query = f"%{query}%"
            cursor.execute(sql, (like_query, like_query, like_query))
            results = cursor.fetchall()
            close_connection(connection)
            return render_template('search_results.html', query=query, results=results)
    return render_template('search.html')

# View users route (Admin only)
@app.route('/view_users')
def view_users():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users")  # Query to get all users
    users = cursor.fetchall()

    close_connection(connection)
    return render_template('view_users.html', users=users)

# View transactions route (Admin only)
@app.route('/view_transactions')
def view_transactions():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM transactions")  # Query to get all transactions
    transactions = cursor.fetchall()

    close_connection(connection)
    return render_template('view_transactions.html', transactions=transactions)

# View logs route (Admin only)
@app.route('/view_logs')
def view_logs():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM admin_logs")  # Query to get all logs
    logs = cursor.fetchall()

    close_connection(connection)
    return render_template('view_logs.html', logs=logs)

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('admin_id', None)  # Remove admin session if it's set
    session.pop('admin_username', None)
    return redirect(url_for('choose_role')) 

if __name__ == '__main__':
    app.run(debug=True)
