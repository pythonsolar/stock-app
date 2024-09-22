from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# ฟังก์ชันสำหรับเชื่อมต่อฐานข้อมูล
def connect_db():
    return sqlite3.connect('stock.db')

# แสดงรายการสินค้าทั้งหมด
@app.route('/')
def index():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM products')
    products = cur.fetchall()
    conn.close()
    return render_template('index.html', products=products)

# เพิ่มสินค้าใหม่
@app.route('/add', methods=['POST'])
def add_product():
    name = request.form['name']
    quantity = request.form['quantity']
    price = request.form['price']
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO products (name, quantity, price) VALUES (?, ?, ?)', (name, quantity, price))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# ฟังก์ชันลบสินค้า
@app.route('/delete/<int:id>')
def delete_product(id):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
