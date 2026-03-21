import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'quotes.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.executescript('''
        CREATE TABLE IF NOT EXISTS directors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_kr TEXT NOT NULL,
            name_en TEXT NOT NULL,
            nationality TEXT,
            birth_year INTEGER,
            famous_works TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            director_id INTEGER NOT NULL,
            quote_original TEXT NOT NULL,
            quote_kr TEXT,
            context TEXT,
            source_url TEXT,
            source_title TEXT,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'COLLECTED',
            FOREIGN KEY (director_id) REFERENCES directors(id)
        );

        CREATE TABLE IF NOT EXISTS scripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_id INTEGER NOT NULL,
            script_kr TEXT,
            script_en TEXT,
            duration_sec INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'SCRIPTED',
            FOREIGN KEY (quote_id) REFERENCES quotes(id)
        );

        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            script_id INTEGER NOT NULL,
            audio_file TEXT,
            video_file TEXT,
            youtube_url TEXT,
            uploaded_at TIMESTAMP,
            status TEXT DEFAULT 'PENDING',
            FOREIGN KEY (script_id) REFERENCES scripts(id)
        );
    ''')

    conn.commit()
    conn.close()
    print("DB 초기화 완료:", os.path.abspath(DB_PATH))

if __name__ == '__main__':
    init_db()
