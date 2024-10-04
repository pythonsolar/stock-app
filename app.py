from flask import Flask, g, render_template, request, redirect, url_for
import sqlite3
import os
from werkzeug.utils import secure_filename

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

# ตั้งค่าที่เก็บไฟล์รูปภาพ
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# ตรวจสอบไฟล์อัปโหลดเป็นชนิดที่อนุญาต
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# เส้นทางสำหรับแสดงหน้าเพิ่มรูปภาพและรายละเอียดสินค้า
@app.route('/product/<int:id>', methods=['GET', 'POST'])
def product_details(id):
    conn = get_db()
    cursor = conn.cursor()

    # ถ้า POST แปลว่าผู้ใช้ส่งฟอร์มมาแล้ว
    if request.method == 'POST':
        detail = request.form['detail']
        file = request.files['image']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # อัปเดตฐานข้อมูล
            cursor.execute('UPDATE products SET detail = ?, image = ? WHERE id = ?', (detail, filename, id))
            conn.commit()

        return redirect(url_for('index'))

    # ดึงข้อมูลสินค้ามาแสดง
    cursor.execute('SELECT * FROM products WHERE id = ?', (id,))
    product = cursor.fetchone()

    return render_template('product_detail.html', product=product)

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
    category = request.form['category']  # รับค่าหมวดหมู่จากฟอร์ม

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO products (name, quantity, price, category) VALUES (?, ?, ?, ?)', (name, quantity, price, category))
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
        category = request.form['category']  # รับค่าหมวดหมู่จากฟอร์ม

        cursor.execute('UPDATE products SET name = ?, quantity = ?, price = ?, category = ? WHERE id = ?', (name, quantity, price, category, id))
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
    app.run(debug=True, port=5001)
