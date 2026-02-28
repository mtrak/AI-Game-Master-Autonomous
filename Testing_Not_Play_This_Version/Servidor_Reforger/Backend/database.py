import sqlite3
import threading
from config import DB_PATH

class WarDatabase:
    def __init__(self):
        self.db_path = DB_PATH
        self.lock = threading.Lock()
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=20.0, check_same_thread=False)
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA synchronous=NORMAL;')
        return conn

    def _init_db(self):
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute('CREATE TABLE IF NOT EXISTS telemetry (id INTEGER PRIMARY KEY CHECK (id=1), px REAL, pz REAL, mission TEXT)')
                c.execute('INSERT OR IGNORE INTO telemetry (id, px, pz, mission) VALUES (1, 4800.0, 6300.0, "Game Master")')
                c.execute('CREATE TABLE IF NOT EXISTS players (name TEXT PRIMARY KEY, px REAL, py REAL, pz REAL)')
                c.execute('CREATE TABLE IF NOT EXISTS troops (id INTEGER PRIMARY KEY, prefab TEXT, px REAL, py REAL, pz REAL)')
                conn.commit()
            finally:
                conn.close() # Siempre se cierra, haya error o no

    def update_telemetry(self, px, pz, m):
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute('UPDATE telemetry SET px=?, pz=?, mission=? WHERE id=1', (px, pz, m))
                conn.commit()
            finally:
                conn.close()

    def get_pos(self):
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute('SELECT px, pz, mission FROM telemetry WHERE id=1')
                res = c.fetchone()
            finally:
                conn.close()
            return res if res else (4800.0, 6300.0, "Game Master")

    def save_state(self, players, troops):
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                for p in players:
                    c.execute('INSERT OR REPLACE INTO players (name, px, py, pz) VALUES (?, ?, ?, ?)', (p['name'], p['px'], p['py'], p['pz']))
                c.execute('DELETE FROM troops')
                for t in troops:
                    if t['prefab']: 
                        c.execute('INSERT INTO troops (id, prefab, px, py, pz) VALUES (?, ?, ?, ?, ?)', (t['id'], t['prefab'], t['px'], t['py'], t['pz']))
                conn.commit()
            finally:
                conn.close()

    def load_state(self):
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute('SELECT id, prefab, px, py, pz FROM troops')
                troops = c.fetchall()
                c.execute('SELECT name, px, py, pz FROM players')
                players = c.fetchall()
            finally:
                conn.close()
            return troops, players

    def get_active_troops(self):
        with self.lock:
            conn = self._get_connection()
            try:
                c = conn.cursor()
                c.execute('SELECT id, prefab, px, pz FROM troops')
                troops = [{"id": row[0], "name": row[1].split('/')[-1].replace('.et', ''), "x": row[2], "z": row[3]} for row in c.fetchall()]
            finally:
                conn.close()
            return troops