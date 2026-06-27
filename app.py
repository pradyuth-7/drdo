import os
import sqlite3
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder='.', static_url_path='')

DATABASE = 'missiles.db'

DEFAULT_MISSILES = [
  { "id": 'agni1',   "name": 'Agni-I',   "cat": 'Ballistic · Short-range',                 "stock": {"G":120,"PL":140,"OS":20, "FT":90, "FP":60, "FC":110,"ICS":80, "ECS":75, "EX":130} },
  { "id": 'agni3',   "name": 'Agni-III', "cat": 'Ballistic · Intermediate-range',          "stock": {"G":150,"PL":160,"OS":140,"FT":130,"FP":120,"FC":150,"ICS":110,"ECS":100,"EX":120} },
  { "id": 'agni5',   "name": 'Agni-V',   "cat": 'Ballistic · Long-range (ICBM-class)',     "stock": {"G":70, "PL":90, "OS":85, "FT":80, "FP":75, "FC":95, "ICS":70, "ECS":65, "EX":90 } },
  { "id": 'akash',   "name": 'Akash',    "cat": 'Surface-to-air',                          "stock": {"G":200,"PL":180,"OS":170,"FT":160,"FP":150,"FC":140,"ICS":130,"ECS":120,"EX":110} },
  { "id": 'brahmos', "name": 'BrahMos',  "cat": 'Cruise · Supersonic',                     "stock": {"G":40, "PL":55, "OS":60, "FT":50, "FP":45, "FC":65, "ICS":48, "ECS":42, "EX":58 } },
  { "id": 'pralay',  "name": 'Pralay',   "cat": 'Quasi-ballistic · Short-range',           "stock": {"G":130,"PL":30, "OS":125,"FT":140,"FP":135,"FC":128,"ICS":120,"ECS":115,"EX":122} },
  { "id": 'nag',     "name": 'Nag',      "cat": 'Anti-tank guided',                        "stock": {"G":95, "PL":88, "OS":92, "FT":76, "FP":70, "FC":99, "ICS":64, "ECS":58, "EX":80 } },
  { "id": 'agnip',   "name": 'Agni-P',   "cat": 'Ballistic · Medium-range (canisterised)', "stock": {"G":160,"PL":155,"OS":150,"FT":145,"FP":140,"FC":135,"ICS":128,"ECS":122,"EX":118} },
  { "id": 'nirbhay', "name": 'Nirbhay',  "cat": 'Cruise · Subsonic',                       "stock": {"G":25, "PL":35, "OS":45, "FT":38, "FP":33, "FC":50, "ICS":30, "ECS":28, "EX":40 } },
  { "id": 'akashng', "name": 'Akash-NG', "cat": 'Surface-to-air · Next-gen',               "stock": {"G":150,"PL":70, "OS":130,"FT":120,"FP":115,"FC":140,"ICS":108,"ECS":102,"EX":135} },
  { "id": 'astra',   "name": 'Astra',    "cat": 'Air-to-air',                              "stock": {"G":110,"PL":105,"OS":98, "FT":88, "FP":82, "FC":96, "ICS":76, "ECS":70, "EX":90 } },
  { "id": 'k15',     "name": 'K-15 (Sagarika)', "cat": 'Submarine-launched ballistic',     "stock": {"G":60, "PL":58, "OS":52, "FT":48, "FP":44, "FC":62, "ICS":40, "ECS":36, "EX":55 } },
]

PARTS_REQ = {
    'G': 1, 'PL': 1, 'OS': 1, 'FT': 2, 'FP': 2, 'FC': 1, 'ICS': 2, 'ECS': 2, 'EX': 1
}

PARTS_LABELS = {
    'G': 'Guidance Module',
    'PL': 'Payload Bay',
    'OS': 'Outer Skin / Airframe',
    'FT': 'Fuel Tanks',
    'FP': 'Fuel Pumps',
    'FC': 'Firing Chamber',
    'ICS': 'Internal Control Surfaces',
    'ECS': 'External Control Surfaces',
    'EX': 'Exhaust / Blast Nozzle'
}

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DATABASE):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS missiles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                cat TEXT NOT NULL,
                forged_count INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS part_stock (
                missile_id TEXT,
                part_code TEXT,
                stock INTEGER,
                PRIMARY KEY (missile_id, part_code),
                FOREIGN KEY (missile_id) REFERENCES missiles (id)
            )
        ''')
        
        # Populate tables with default data
        for m in DEFAULT_MISSILES:
            cursor.execute(
                'INSERT INTO missiles (id, name, cat, forged_count) VALUES (?, ?, ?, 0)',
                (m['id'], m['name'], m['cat'])
            )
            for part_code, stock in m['stock'].items():
                cursor.execute(
                    'INSERT INTO part_stock (missile_id, part_code, stock) VALUES (?, ?, ?)',
                    (m['id'], part_code, stock)
                )
        
        conn.commit()
        conn.close()
        print("Database initialized successfully.")

# Initialize database
init_db()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/drdo-missile-production-control (1).html')
def index_legacy():
    return send_from_directory('.', 'index.html')

@app.route('/api/missiles', methods=['GET'])
def get_missiles():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query missiles
    cursor.execute('SELECT * FROM missiles')
    missiles_rows = cursor.fetchall()
    
    # Query all stocks
    cursor.execute('SELECT missile_id, part_code, stock FROM part_stock')
    stocks_rows = cursor.fetchall()
    
    conn.close()
    
    # Group stocks by missile_id
    stocks_by_missile = {}
    for row in stocks_rows:
        mid = row['missile_id']
        if mid not in stocks_by_missile:
            stocks_by_missile[mid] = {}
        stocks_by_missile[mid][row['part_code']] = row['stock']
        
    result = []
    for m in missiles_rows:
        mid = m['id']
        result.append({
            'id': mid,
            'name': m['name'],
            'cat': m['cat'],
            'forged_count': m['forged_count'],
            'stock': stocks_by_missile.get(mid, {})
        })
        
    return jsonify(result)

@app.route('/api/missiles/<missile_id>/forge', methods=['POST'])
def forge_missile(missile_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if missile exists
    cursor.execute('SELECT name FROM missiles WHERE id = ?', (missile_id,))
    missile = cursor.fetchone()
    if not missile:
        conn.close()
        return jsonify({'error': 'Missile not found'}), 404
    
    missile_name = missile['name']
    
    # Start transaction (implicitly managed by context/commit in SQLite connection)
    try:
        # Fetch current stock for all parts of this missile
        cursor.execute('SELECT part_code, stock FROM part_stock WHERE missile_id = ?', (missile_id,))
        rows = cursor.fetchall()
        current_stock = {row['part_code']: row['stock'] for row in rows}
        
        # Check if all required parts exist and have enough stock
        insufficient_parts = []
        for part_code, req_qty in PARTS_REQ.items():
            stock = current_stock.get(part_code, 0)
            if stock < req_qty:
                insufficient_parts.append(PARTS_LABELS.get(part_code, part_code))
                
        if insufficient_parts:
            conn.close()
            parts_str = ', '.join(insufficient_parts)
            return jsonify({'error': f'Not enough materials: {parts_str} is over so can\'t make more missiles'}), 400
            
        # Sufficient stock! Decrement stocks and increment forged count
        for part_code, req_qty in PARTS_REQ.items():
            cursor.execute(
                'UPDATE part_stock SET stock = stock - ? WHERE missile_id = ? AND part_code = ?',
                (req_qty, missile_id, part_code)
            )
            
        cursor.execute(
            'UPDATE missiles SET forged_count = forged_count + 1 WHERE id = ?',
            (missile_id,)
        )
        
        conn.commit()
        
        # Determine if any parts are now depleted (less than required for another unit)
        cursor.execute('SELECT part_code, stock FROM part_stock WHERE missile_id = ?', (missile_id,))
        updated_rows = cursor.fetchall()
        updated_stock = {row['part_code']: row['stock'] for row in updated_rows}
        
        depleted_parts = []
        for part_code, req_qty in PARTS_REQ.items():
            if updated_stock.get(part_code, 0) < req_qty:
                depleted_parts.append({
                    'code': part_code,
                    'label': PARTS_LABELS.get(part_code, part_code)
                })
                
        conn.close()
        return jsonify({
            'success': True,
            'message': f'Successfully forged 1 {missile_name}!',
            'depleted_parts': depleted_parts
        })
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
