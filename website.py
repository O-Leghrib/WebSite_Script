from flask import Flask, render_template, request, send_file
import mysql.connector
import csv
import io
import pandas as pd
import os
import re

app = Flask(__name__)

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1705",
        database="profiles_info"
    )

def clean_illegal_chars(value):
    if isinstance(value, str):
        # Remove all control characters except \n, \r, \t
        return re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', value)
    return value

@app.route('/', methods=['GET', 'POST'])
def search():
    results = []
    keyword = ""
    result_count = 0

    if request.method == 'POST' and request.form['action'] == 'search':
        keyword = request.form['keyword']
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT
            person.user_id,
            person.display_name,
            person.username,
            person.email,
            person.created_at AS person_created,
            person.phone,
            announce.title,
            announce.description,
            announce.created_at AS announce_created,
            announce.city,
            announce.price
        FROM person
        LEFT JOIN announce ON person.user_id = announce.user_id
        WHERE
            person.user_id LIKE %s OR
            person.display_name LIKE %s OR
            person.username LIKE %s OR
            person.email LIKE %s OR
            person.created_at LIKE %s OR
            person.phone LIKE %s OR
            announce.title LIKE %s OR
            announce.description LIKE %s OR
            announce.created_at LIKE %s OR
            announce.city LIKE %s OR
            announce.price LIKE %s
        """
        wildcard = f"%{keyword}%"
        params = [wildcard] * 11
        cursor.execute(query, params)
        results = cursor.fetchall()
        result_count = len(results)

        if results:
            # Save CSV
            with open('temp_results.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)

            # Save Excel (clean illegal characters)
            df = pd.DataFrame(results)
            df = df.applymap(clean_illegal_chars)
            df.to_excel('temp_results.xlsx', index=False)

        cursor.close()
        conn.close()

    return render_template('search.html', results=results, keyword=keyword, result_count=result_count)

@app.route('/download/csv')
def download_csv():
    if os.path.exists('temp_results.csv'):
        return send_file('temp_results.csv', as_attachment=True)
    return "CSV not available", 404

@app.route('/download/excel')
def download_excel():
    if os.path.exists('temp_results.xlsx'):
        return send_file('temp_results.xlsx', as_attachment=True)
    return "Excel not available", 404

if __name__ == '__main__':
    app.run(port=8000, debug=True)