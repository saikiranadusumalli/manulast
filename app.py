from flask import Flask, request, jsonify, render_template
import pyodbc
import os
import pandas as pd
import matplotlib.pyplot as plt

app = Flask(__name__)

server = 'manub.database.windows.net'
database = 'quiz5'
username = 'manub'
password = 'Arjunsuha1*'
driver = '{ODBC Driver 17 for SQL Server}'

def get_db_connection():
    conn = pyodbc.connect('DRIVER=' + driver + 
                          ';SERVER=' + server + 
                          ';PORT=1433;DATABASE=' + database + 
                          ';UID=' + username + 
                          ';PWD=' + password)
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/food', methods=['GET'])
def get_food():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM food')
    rows = cursor.fetchall()
    food_items = [{'food': row[0], 'quantity': row[1], 'price': row[2]} for row in rows]
    conn.close()
    return jsonify(food_items)

@app.route('/food', methods=['POST'])
def add_food():
    data = request.get_json()
    food = data['food']
    quantity = data['quantity']
    price = data['price']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('MERGE INTO food AS target '
                   'USING (SELECT ? AS food) AS source '
                   'ON target.food = source.food '
                   'WHEN MATCHED THEN '
                   'UPDATE SET quantity = ?, price = ? '
                   'WHEN NOT MATCHED THEN '
                   'INSERT (food, quantity, price) VALUES (?, ?, ?);', 
                   (food, quantity, price, food, quantity, price))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Food item added or updated successfully'})

@app.route('/food', methods=['DELETE'])
def delete_food():
    data = request.get_json()
    food = data['food']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM food WHERE food = ?', (food,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Food item deleted successfully'})

@app.route('/plot_pie_chart/<int:N>')
def plot_pie_chart(N):
    conn = get_db_connection()
    df = pd.read_sql('SELECT * FROM food', conn)
    conn.close()
    largest_quantities = df.nlargest(N, 'quantity')
    plt.figure(figsize=(10, 7))
    plt.pie(largest_quantities['quantity'], labels=largest_quantities.apply(lambda x: f"{x['food']} ({x['quantity']})", axis=1), autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
    plt.title(f"Top {N} Foods by Quantity")
    plt.savefig('static/pie_chart.png')
    plt.close()
    return render_template('plot.html', plot_url='pie_chart.png')

@app.route('/plot_bar_chart/<int:N>')
def plot_bar_chart(N):
    conn = get_db_connection()
    df = pd.read_sql('SELECT * FROM food', conn)
    conn.close()
    
    most_expensive = df.nlargest(N, 'price')
    most_expensive = most_expensive[::-1]  # Reverse the dataframe order
    
    plt.figure(figsize=(10, 7))
    bars = plt.barh(most_expensive['food'], most_expensive['price'], color='red')
    plt.xlabel('Price')
    plt.ylabel('Food')
    plt.title(f"Top {N} Most Expensive Foods (Reversed)")
    
    for bar in bars:
        plt.text(bar.get_width() - bar.get_width() * 0.5, bar.get_y() + bar.get_height()/2, f'{bar.get_width()}', ha='right', va='right', color='white')
    
    plt.savefig('static/bar_chart.png')
    plt.close()
    
    return render_template('plot.html', plot_url='bar_chart.png')

@app.route('/points', methods=['GET'])
def get_points():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM points')
    rows = cursor.fetchall()
    points = [{'x': row[0], 'y': row[1], 'quantity': row[2]} for row in rows]
    conn.close()
    return jsonify(points)

@app.route('/points', methods=['POST'])
def add_point():
    data = request.get_json()
    x = data['x']
    y = data['y']
    quantity = data['quantity']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO points (x, y, quantity) VALUES (?, ?, ?);', 
                   (x, y, quantity))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Point added successfully'})

@app.route('/plot_scatter')
def plot_scatter():
    conn = get_db_connection()
    df = pd.read_sql('SELECT * FROM points', conn)
    conn.close()
    colors = df['quantity'].apply(lambda q: 'red' if q < 100 else 'blue' if q < 1000 else 'green')
    plt.figure(figsize=(10, 7))
    plt.scatter(df['x'], df['y'], c=colors)
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Scatter Plot of Points')
    plt.savefig('static/scatter_plot.png')
    plt.close()
    return render_template('plot.html', plot_url='scatter_plot.png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
