from flask import Flask, g, render_template, request, redirect, url_for
import sqlite3
import os
from werkzeug.utils import secure_filename
import random
from datetime import datetime

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

        # ตรวจสอบว่าอัปโหลดไฟล์หรือไม่
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # อัปเดตทั้งรูปภาพและรายละเอียด
            cursor.execute('UPDATE products SET detail = ?, image = ? WHERE id = ?', (detail, filename, id))
        else:
            # อัปเดตเฉพาะรายละเอียดสินค้า ถ้าไม่มีการอัปโหลดไฟล์ใหม่
            cursor.execute('UPDATE products SET detail = ? WHERE id = ?', (detail, id))

        conn.commit()
        return redirect(url_for('index'))

    # ดึงข้อมูลสินค้าที่มี id ตรงกับที่ระบุ
    cursor.execute('SELECT * FROM products WHERE id = ?', (id,))
    product_row = cursor.fetchone()

    # ถ้าไม่พบสินค้าตาม id ให้แจ้งว่าไม่มีสินค้า
    if product_row is None:
        return "Product not found", 404

    # จัดข้อมูลเป็น dictionary เพื่อให้เข้าถึงด้วยชื่อฟิลด์
    product = {
        'id': product_row[0],
        'name': product_row[1],
        'quantity': product_row[2],
        'price': product_row[3],
        'category': product_row[4],
        'image': product_row[5],
        'detail': product_row[6]
    }

    return render_template('product_detail.html', product=product)

# หน้าหลักแสดงรายการสินค้า
@app.route('/')
def index():
    conn = get_db()
    cursor = conn.cursor()

    # รับค่าค้นหาจาก query string (แยก name และ category)
    search_name = request.args.get('search', '').strip()
    search_category = request.args.get('category', '')

    # สร้างคำสั่ง SQL แบบ dynamic ตามเงื่อนไขที่มี
    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if search_name:  # ถ้ามีการค้นหาด้วยชื่อ
        query += " AND name LIKE ?"
        params.append(f"%{search_name}%")

    if search_category:  # ถ้ามีการเลือก category
        query += " AND category = ?"
        params.append(search_category)

    # Execute the final SQL query with the parameters
    cursor.execute(query, params)
    
    # ดึงข้อมูลจากฐานข้อมูล
    products_rows = cursor.fetchall()

    # จัดรูปแบบข้อมูลเป็น dictionary เพื่อเข้าถึงด้วยชื่อฟิลด์
    products = []
    for row in products_rows:
        products.append({
            'id': row[0],
            'name': row[1],
            'quantity': row[2],
            'price': row[3],
            'category': row[4],
            'image': row[5],
            'detail': row[6],
            'product_code': row[7]
        })

    conn.close()
    
    return render_template('index.html', products=products)


# แสดงหน้าเพิ่มสินค้าใหม่
@app.route('/add_product_page', methods=['GET'])
def add_product_page():
    return render_template('add_product.html')  # ใช้เทมเพลต add_product.html

# ฟังก์ชันเพิ่มสินค้าใหม่
@app.route('/add', methods=['POST'])
def add_product():
    name = request.form['name']
    quantity = request.form['quantity']
    price = request.form['price']
    category = request.form['category']

    # สร้างรหัสสินค้า product_code (เช่น kc2024100556)
    today = datetime.today().strftime('%Y%m%d')  # ปี, เดือน, วัน
    random_number = str(random.randint(10, 99))  # สุ่มเลข 2 หลัก
    product_code = f"kc{today}{random_number}"  # รวมกันเป็น kcYYYYMMDDxx
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO products (name, quantity, price, category, product_code) VALUES (?, ?, ?, ?, ?)',
                   (name, quantity, price, category, product_code))
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
        category = request.form['category']

        cursor.execute('UPDATE products SET name = ?, quantity = ?, price = ?, category = ? WHERE id = ?', (name, quantity, price, category, id))
        conn.commit()
        return redirect(url_for('index'))

    # ดึงข้อมูลสินค้าจากฐานข้อมูล
    cursor.execute('SELECT * FROM products WHERE id = ?', (id,))
    product_row = cursor.fetchone()

    # แปลงข้อมูลเป็น dictionary เพื่อส่งไปยัง template
    product = {
        'id': product_row[0],
        'name': product_row[1],
        'quantity': product_row[2],
        'price': product_row[3],
        'category': product_row[4]
    }

    return render_template('edit.html', product=product)

# ฟังก์ชันลบสินค้า
@app.route('/delete/<int:id>')
def delete_product(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    return redirect(url_for('index'))

def generate_product_code():
    # ดึงวันที่ปัจจุบัน
    current_date = datetime.datetime.now()
    
    # แปลงวันที่ปัจจุบันเป็นฟอร์แมต ปี, เดือน, วัน
    year = current_date.strftime("%Y")  # ปี ค.ศ.
    month = current_date.strftime("%m")  # เดือน 2 หลัก
    day = current_date.strftime("%d")    # วัน 2 หลัก
    
    # สุ่มตัวเลข 2 หลักท้าย
    random_number = random.randint(10, 99)  # สุ่มเลข 2 หลัก เช่น 12, 98
    
    # รวมเป็นรหัสสินค้า 12 หลัก
    product_code = f"KC{year}{month}{day}{random_number}"
    
    return product_code

def generate_unique_product_code():
    conn = get_db()
    cursor = conn.cursor()
    
    while True:
        product_code = generate_product_code()
        
        # ตรวจสอบว่ารหัสสินค้าซ้ำหรือไม่
        cursor.execute("SELECT COUNT(*) FROM products WHERE product_code = ?", (product_code,))
        result = cursor.fetchone()
        
        # ถ้ารหัสไม่ซ้ำ ให้ใช้รหัสนี้
        if result[0] == 0:
            return product_code

if __name__ == '__main__':
    app.run(debug=True, port=5001)

