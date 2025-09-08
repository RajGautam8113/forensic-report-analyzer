# app/models.py

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '../data/forensic_reports.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            extracted_text TEXT,
            name TEXT,
            age TEXT,
            gender TEXT,
            address TEXT,
            date_of_death TEXT,
            cause_of_death TEXT,
            examiner TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_report(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reports (filename, extracted_text, name, age, gender, address, date_of_death, cause_of_death, examiner)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('filename'),
        data.get('extracted_text'),
        data.get('Name'),
        data.get('Age'),
        data.get('Gender'),
        data.get('Address'),
        data.get('Date of Death'),
        data.get('Cause of Death'),
        data.get('Examiner'),
    ))
    conn.commit()
    conn.close()

def get_all_reports():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, filename, name, age, gender, date_of_death FROM reports ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_report_by_id(report_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reports WHERE id = ?', (report_id,))
    row = cursor.fetchone()
    conn.close()
    return row
