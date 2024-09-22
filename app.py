from flask import Flask, g, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

DATABASE = 'stock.db'

# ฟังก์ชันสำหรับเชื่อมต่อกับฐานข้อมูล
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# ฟังก์ชันปิดการเชื่อมต่อ
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# หน้าหลักแสดงรายการสินค้า
@app.route('/')
def index():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    return render_template('index.html', products=products)

# ฟังก์ชันเพิ่มสินค้าใหม่
@app.route('/add', methods=['POST'])
def add_product():
    name = request.form['name']
    quantity = request.form['quantity']
    price = request.form['price']

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO products (name, quantity, price) VALUES (?, ?, ?)', (name, quantity, price))
    conn.commit()

    return redirect(url_for('index'))

# ฟังก์ชันแก้ไขสินค้า
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        price = request.form['price']
        cursor.execute('UPDATE products SET name = ?, quantity = ?, price = ? WHERE id = ?', (name, quantity, price, id))
        conn.commit()
        return redirect(url_for('index'))

    cursor.execute('SELECT * FROM products WHERE id = ?', (id,))
    product = cursor.fetchone()
    return render_template('edit.html', product=product)

# ฟังก์ชันลบสินค้า
@app.route('/delete/<int:id>')
def delete_product(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
