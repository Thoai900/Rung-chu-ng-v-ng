from flask import Flask, render_template, request, jsonify, session
import mysql.connector
import random
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'rung_chuong_vang_secret_key') # Needed for session

# Cấu hình kết nối MySQL
db_config = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'Thoai12345'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'rung_chuong_vang'),
    'port': os.getenv('DB_PORT', 3306)
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/leaderboard')
def leaderboard_page():
    return render_template('leaderboard.html')

# --- API Endpoints ---

@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM questions")
    categories = [row[0] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    return jsonify(categories)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    name = data.get('name')
    group = data.get('group') # Class

    if not name or not group:
        return jsonify({'error': 'Missing name or class'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = conn.cursor()
    # Log student login
    query = "INSERT INTO students (full_name, class_name) VALUES (%s, %s)"
    cursor.execute(query, (name, group))
    conn.commit()
    
    cursor.close()
    conn.close()
    return jsonify({'message': 'Login successful'})


@app.route('/api/questions', methods=['GET'])
def get_questions():
    category = request.args.get('category')
    mode = request.args.get('mode') # 'play' or 'review'
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    limit_clause = "LIMIT 20"
    if mode == 'review':
        limit_clause = "" # No limit for review

    if category:
        query = f"SELECT * FROM questions WHERE category = %s ORDER BY RAND() {limit_clause}"
        cursor.execute(query, (category,))
    else:
        query = f"SELECT * FROM questions ORDER BY RAND() {limit_clause}"
        cursor.execute(query)
        
    questions = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return jsonify(questions)

@app.route('/api/submit', methods=['POST'])
def submit_result():
    data = request.json
    name = data.get('name')
    group = data.get('group') # Lớp
    score = data.get('score')
    time_spent = data.get('time_spent')
    
    if not name or not group:
         return jsonify({'error': 'Missing name or class'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    cursor = conn.cursor()
    query = "INSERT INTO exam_results (student_name, class_name, score, total_time) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (name, group, score, time_spent))
    conn.commit()
    
    cursor.close()
    conn.close()
    return jsonify({'message': 'Result saved successfully'})

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
        
    cursor = conn.cursor(dictionary=True)
    # Order by Score DESC, then Time ASC, but group by student to show only best result
    query = """
        SELECT student_name, class_name, MAX(score) as score, MIN(total_time) as total_time, MAX(created_at) as created_at
        FROM exam_results 
        GROUP BY student_name, class_name 
        ORDER BY score DESC, total_time ASC 
        LIMIT 10
    """
    cursor.execute(query)
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return jsonify(results)

@app.route('/admin/login')
def admin_login_page():
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    # Simple session check (In prod, use a proper decorator)
    if 'admin_id' not in session:
        return redirect('/admin/login')
    return render_template('admin_dashboard.html', role=session.get('role'))

@app.route('/api/admin/auth', methods=['POST'])
def admin_auth():
    data = request.json
    email = data.get('email')
    # In a real app, verify Firebase ID Token here. 
    # For MVP, we trust the email sent from client (after firebase auth success)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
    admin = cursor.fetchone()
    
    if not admin:
        # Auto-register as Editor? Or deny? 
        # Requirement says "admin needs password/account saved".
        # Let's auto-register first time users as 'editor' for ease, 
        # or reject if strictly pre-approved. 
        # Let's AUTO-REGISTER as 'editor' for MVP smoothness.
        cursor.execute("INSERT INTO admins (email, role) VALUES (%s, 'editor')", (email,))
        conn.commit()
        admin_id = cursor.lastrowid
        role = 'editor'
    else:
        admin_id = admin['id']
        role = admin['role']
    
    cursor.close()
    conn.close()
    
    session['admin_id'] = admin_id
    session['role'] = role
    
    return jsonify({'message': 'Logged in', 'role': role})

@app.route('/api/admin/pending', methods=['GET'])
def get_pending_changes():
    if 'admin_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, a.email as admin_email 
        FROM pending_changes p 
        JOIN admins a ON p.admin_id = a.id 
        WHERE p.status = 'PENDING'
        ORDER BY p.created_at DESC
    """)
    changes = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(changes)

@app.route('/api/admin/approve', methods=['POST'])
def approve_change():
    if 'admin_id' not in session or session.get('role') != 'super_admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.json
    change_id = data.get('change_id')
    action = data.get('action') # 'APPORVE' or 'REJECT'
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM pending_changes WHERE id = %s", (change_id,))
    change = cursor.fetchone()
    
    if not change:
        return jsonify({'error': 'Change not found'}), 404
        
    if action == 'REJECT':
        cursor.execute("UPDATE pending_changes SET status = 'REJECTED' WHERE id = %s", (change_id,))
        conn.commit()
    elif action == 'APPROVE':
        import json
        content = json.loads(change['new_content_json'])
        
        if change['action_type'] == 'CREATE':
             cursor.execute(
                 "INSERT INTO questions (category, content, options, answer, type) VALUES (%s, %s, %s, %s, %s)",
                 (content['category'], content['content'], content.get('options', ''), content['answer'], content['type'])
             )
        elif change['action_type'] == 'UPDATE':
             cursor.execute(
                 "UPDATE questions SET category=%s, content=%s, options=%s, answer=%s, type=%s WHERE id=%s",
                 (content['category'], content['content'], content.get('options', ''), content['answer'], content['type'], change['question_id'])
             )
        elif change['action_type'] == 'DELETE':
             cursor.execute("DELETE FROM questions WHERE id = %s", (change['question_id'],))
             
        cursor.execute("UPDATE pending_changes SET status = 'APPROVED' WHERE id = %s", (change_id,))
        conn.commit()
        
    cursor.close()
    conn.close()
    return jsonify({'message': 'Processed'})

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin_id', None)
    session.pop('role', None)
    return jsonify({'message': 'Logged out'})

@app.route('/api/admin/questions/create', methods=['POST'])
def admin_create_questions():
    if 'admin_id' not in session: 
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    questions = data.get('questions', [])
    
    if not questions:
        return jsonify({'error': 'No questions provided'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql = "INSERT INTO questions (category, content, options, answer, type) VALUES (%s, %s, %s, %s, %s)"
    vals = []
    
    for q in questions:
        # q should have: category, content, options, answer, type
        vals.append((
            q.get('category', 'Chung'),
            q.get('content'),
            q.get('options', ''),
            q.get('answer'),
            q.get('type', 'trac_nghiem')
        ))
        
    cursor.executemany(sql, vals)
    conn.commit()
    inserted = cursor.rowcount
    
    cursor.close()
    conn.close()
    
    return jsonify({'message': f'Successfully inserted {inserted} questions'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
