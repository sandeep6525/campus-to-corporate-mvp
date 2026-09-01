from sqlalchemy import text
from app.db import engine

def column_exists(conn, table, column):
    res = conn.execute(text(f"PRAGMA table_info('{table}')")).all()
    return any(r[1] == column for r in res)

def ensure_difficulty_column():
    with engine.connect() as conn:
        if not column_exists(conn, 'sessions', 'difficulty_level'):
            conn.execute(text("ALTER TABLE sessions ADD COLUMN difficulty_level TEXT DEFAULT 'medium'"))
            print('Added difficulty_level column to sessions')
        else:
            print('difficulty_level column already present')

def ensure_media_table():
    create_sql = '''
    CREATE TABLE IF NOT EXISTS media_assets (
        id INTEGER PRIMARY KEY,
        answer_id INTEGER UNIQUE,
        media_type TEXT,
        file_name TEXT,
        file_url TEXT,
        transcription_text TEXT,
        duration_seconds INTEGER,
        byte_size INTEGER,
        playback_count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    '''
    with engine.connect() as conn:
        conn.execute(text(create_sql))
        print('Ensured media_assets table exists')

def main():
    ensure_difficulty_column()
    ensure_media_table()

if __name__ == '__main__':
    main()
