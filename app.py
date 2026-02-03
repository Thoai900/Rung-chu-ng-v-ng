from flask import Flask, render_template, request, jsonify, session, redirect
import mysql.connector
import random
import os
import string
from dotenv import load_dotenv
from flask_socketio import SocketIO, emit, join_room as join_room_socket, leave_room as leave_room_socket

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'rung_chuong_vang_secret_key') # Needed for session
socketio = SocketIO(app, cors_allowed_origins="*")

# Cấu hình kết nối MySQL
db_config = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'Thoai12345'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'rung_chuong_vang'),
    'port': os.getenv('DB_PORT', 3306)
}

# --- In-Memory Game State ---
rooms = {} 
# Structure:
# {
#   'ROOM_ID': {
#       'host_sid': 'sid',
#       'state': 'waiting' | 'playing' | 'finished',
#       'players': { 'sid': { 'name': '...', 'score': 0, 'answered': False } },
#       'questions': [ { ... } ],
#       'current_q_index': 0,
#       'category': '...'
#   }
# }

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

@app.route('/battle')
def battle_page():
    return render_template('battle_app.html')

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
    
    # Support single question creation too
    if not questions and 'content' in data:
        questions = [data]

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

@app.route('/api/admin/stats', methods=['GET'])
def admin_get_stats():
    if 'admin_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM questions")
    total_questions = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    active_rooms = len(rooms)
    
    return jsonify({
        'total_students': total_students,
        'total_questions': total_questions,
        'active_rooms': active_rooms
    })

@app.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    if 'admin_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students ORDER BY login_time DESC LIMIT 100") # Limit for perf
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(users)

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    if 'admin_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message': 'User deleted'})

@app.route('/api/admin/rooms', methods=['GET'])
def admin_get_rooms():
    if 'admin_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    # Convert active rooms dict to list
    room_list = []
    for code, room in rooms.items():
        room_list.append({
            'code': code,
            'host': room['players'][room['host_sid']]['name'],
            'players_count': len(room['players']),
            'state': room['state'],
            'category': room['category']
        })
        
    return jsonify(room_list)

@app.route('/api/admin/rooms/<code>', methods=['DELETE'])
def admin_delete_room(code):
    if 'admin_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    if code in rooms:
        # Emit event to all players in room that it's closed
        socketio.emit('error', {'message': 'Phòng đã bị Admin đóng!'}, room=code)
        # Maybe force redirect all clients?
        del rooms[code]
        return jsonify({'message': 'Room closed'})
    
    return jsonify({'error': 'Room not found'}), 404

# --- Direct Question CRUD for Admin ---

@app.route('/api/admin/questions/<int:q_id>', methods=['PUT'])
def admin_update_question(q_id):
    if 'admin_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE questions SET category=%s, content=%s, options=%s, answer=%s, type=%s WHERE id=%s",
        (data['category'], data['content'], data.get('options', ''), data['answer'], data['type'], q_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Question updated'})

@app.route('/api/admin/questions/<int:q_id>', methods=['DELETE'])
def admin_delete_question(q_id):
    if 'admin_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM questions WHERE id = %s", (q_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Question deleted'})

# --- SocketIO Events ---

@socketio.on('create_room')
def handle_create_room(data):
    # data: { 'host_name': ..., 'category': ... }
    room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    host_name = data.get('host_name')
    category = data.get('category')
    
    rooms[room_code] = {
        'host_sid': request.sid,
        'state': 'waiting',
        'players': { request.sid: { 'name': host_name, 'score': 0, 'answered': False, 'is_host': True, 'eliminated': False } },
        'questions': [], # To be loaded
        'current_q_index': 0,
        'category': category,
        'active_players_count': 1
    }
    
    join_room_socket(room_code)
    emit('room_created', {'room_code': room_code, 'players': [p for p in rooms[room_code]['players'].values()]}, room=room_code)

@socketio.on('join_room')
def handle_join_room(data):
    room_code = data.get('room_code').upper()
    player_name = data.get('player_name')
    
    if room_code not in rooms:
        emit('error', {'message': 'Phòng không tồn tại!'})
        return
        
    room = rooms[room_code]
    if room['state'] != 'waiting':
        emit('error', {'message': 'Trận đấu đang diễn ra!'})
        return
        
    join_room_socket(room_code)
    room['players'][request.sid] = { 'name': player_name, 'score': 0, 'answered': False, 'is_host': False, 'eliminated': False }
    room['active_players_count'] += 1
    
    # Broadcast list of players
    player_list = [p for p in room['players'].values()]
    emit('player_joined', {'players': player_list}, room=room_code)

@socketio.on('start_game')
def handle_start_game(data):
    room_code = data.get('room_code')
    room = rooms.get(room_code)
    
    if not room or room['host_sid'] != request.sid:
        return
        
    # Load questions from DB
    category = room['category']
    mode = 'play' 
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Battle Mode: Random 10 questions from ALL categories
    query = "SELECT * FROM questions ORDER BY RAND() LIMIT 10"
    cursor.execute(query)
        
    room['questions'] = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not room['questions']:
        emit('error', {'message': 'Không có câu hỏi!'}, room=room_code)
        return

    room['state'] = 'playing'
    room['current_q_index'] = 0
    
    # Broadcast first question
    send_question(room_code)

def send_question(room_code):
    room = rooms[room_code]
    idx = room['current_q_index']
    
    if idx >= len(room['questions']):
        # Game Over: End of questions
        room['state'] = 'finished'
        sorted_final = sorted(room['players'].values(), key=lambda x: x['score'], reverse=True)
        emit('game_over', {'leaderboard': sorted_final, 'reason': 'finished'}, room=room_code)
        return

    q = room['questions'][idx]
    
    # Reset answer status
    for p in room['players'].values():
        p['answered'] = False
        p['current_answer'] = None

    # Only count non-eliminated players for answer tracking
    active_count = sum(1 for p in room['players'].values() if not p.get('eliminated'))
    room['should_answer_count'] = active_count
    
    # If only 1 player left (and we didn't catch it yet), they win automatically? 
    # Or we let them play single player? "Rung chuong vang" usually ends.
    # Logic handled in process_round, but let's check here too to be safe.
    if active_count <= 1 and len(room['players']) > 1:
        # Check if we should end
        pass # Handle in process_result for consistency

    emit('new_question', {
        'question': q['content'],
        'options': q['options'],
        'type': q['type'], # tu_luan or trac_nghiem
        'index': idx + 1,
        'total': len(room['questions']),
        'time_limit': 15,
        'active_players': active_count
    }, room=room_code)

@socketio.on('submit_answer')
def handle_answer(data):
    room_code = data.get('room_code')
    answer = data.get('answer')
    
    room = rooms.get(room_code)
    if not room or request.sid not in room['players']:
        return
        
    player = room['players'][request.sid]
    if player.get('eliminated') or player['answered']: return 
    
    player['answered'] = True
    player['current_answer'] = answer
    
    # Notify host/everyone that this user answered (but hide result)
    emit('player_answered', {'sid': request.sid}, room=room_code)
    
    # Check if all active players answered
    active_players = [p for p in room['players'].values() if not p.get('eliminated')]
    answered_count = sum(1 for p in active_players if p['answered'])
    
    if answered_count >= len(active_players):
        process_round_result(room_code)

def process_round_result(room_code):
    room = rooms.get(room_code)
    if not room: return
    
    q = room['questions'][room['current_q_index']]
    correct_content = q['answer']
    
    # Evaluation
    eliminated_in_this_round = []
    
    active_players = [p for p in room['players'].values() if not p.get('eliminated')]
    
    for p in active_players:
        ans = p.get('current_answer', '')
        is_correct = False
        
        if q['type'] == 'tu_luan':
             if ans.strip().lower() == correct_content.strip().lower():
                 is_correct = True
        else:
             # Multiple choice check
             choice_prefix = ans.split('.')[0].strip().upper() if ans else ''
             correct_prefix = correct_content.split('.')[0].strip().upper()
             if (ans == correct_content) or (choice_prefix == correct_prefix):
                 is_correct = True
        
        if is_correct:
            p['score'] += 10
        else:
            p['eliminated'] = True
            eliminated_in_this_round.append(p['name'])
            
    # Remaining active players
    remaining = [p for p in room['players'].values() if not p.get('eliminated')]
    
    # Broadcast Round Result
    emit('round_result', {
        'correct_answer': correct_content,
        'eliminated': eliminated_in_this_round,
        'remaining_count': len(remaining),
        'leaderboard': sorted(room['players'].values(), key=lambda x: x['score'], reverse=True)
    }, room=room_code)
    
    # Check Game Over Conditions
    if len(remaining) == 1 and len(room['players']) > 1:
        # WINNER (if multiplayer)
        room['state'] = 'finished'
        emit('game_over', {'winner': remaining[0], 'reason': 'last_man'}, room=room_code)
    elif len(remaining) == 0:
        # DRAW (All died same round)
        room['state'] = 'finished'
        emit('game_over', {'reason': 'draw'}, room=room_code)
    elif room['current_q_index'] >= len(room['questions']) - 1:
        # End of questions
        room['state'] = 'finished'
        # Sort by Score
        sorted_final = sorted(room['players'].values(), key=lambda x: x['score'], reverse=True)
        emit('game_over', {'leaderboard': sorted_final, 'reason': 'finished'}, room=room_code)
    else:
        # Auto-trigger next question after 5s
        socketio.sleep(5)
        # Check state again in case valid
        if room['state'] == 'playing':
             room['current_q_index'] += 1
             send_question(room_code)

@socketio.on('round_timeout')
def handle_round_timeout(data):
    # Host tells us time is up, force process round
    room_code = data.get('room_code')
    room = rooms.get(room_code)
    if room and room['host_sid'] == request.sid:
         # Double check if round already processed? 
         # process_round_result is idempotent-ish if answered status reset logic is handled carefully.
         # But here we rely on 'current_q_index'.
         process_round_result(room_code)

@socketio.on('next_question')
def handle_next(data):
    room_code = data.get('room_code')
    room = rooms.get(room_code)
    if not room or room['host_sid'] != request.sid: return
    
    room['current_q_index'] += 1
    send_question(room_code)
    

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
