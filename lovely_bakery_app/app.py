import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'lovely_bakery_secret_key_stark'

# डिफ़ॉल्ट मेनू आइटम्स
menu_database = [
    {
        "id": 1,
        "name": "Choco Truffle Gold Cake",
        "price": "699",
        "weight": "1 Pound (500g)",
        "image": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500&auto=format&fit=crop&q=60"
    },
    {
        "id": 2,
        "name": "Royal Red Velvet Pastry",
        "price": "199",
        "weight": "250g",
        "image": "https://images.unsplash.com/photo-1586985289688-ca3cf47d3e6e?w=500&auto=format&fit=crop&q=60"
    }
]

# ऑर्डर्स डेटाबेस
orders_database = [
    {
        "id": 1, 
        "name": "Rahul Sharma", 
        "phone": "9876543210", 
        "item": "Choco Truffle Gold Cake (1 Pound (500g))", 
        "quantity": 1, 
        "location": "Civil Lines, Bareilly", 
        "status": "Pending"
    }
]

@app.route('/')
def index():
    return render_template('index.html', menu=menu_database)

@app.route('/place_order', methods=['POST'])
def place_order():
    name = request.form.get('customer_name')
    phone = request.form.get('customer_phone')
    item = request.form.get('cake_item')
    quantity = request.form.get('quantity')
    location = request.form.get('customer_location')
    
    new_id = max((o['id'] for o in orders_database), default=0) + 1

    new_order = {
        "id": new_id,
        "name": name,
        "phone": phone,
        "item": item,
        "quantity": int(quantity),
        "location": location,
        "status": "Pending"
    }
    orders_database.append(new_order)
    return jsonify({"success": True, "order_id": new_id, "message": "Order placed successfully!"})

@app.route('/track_order', methods=['POST'])
def track_order():
    try:
        order_id = int(request.form.get('order_id'))
        order = next((o for o in orders_database if o['id'] == order_id), None)
        if order:
            return jsonify({"success": True, "order": order})
        else:
            return jsonify({"success": False, "message": "Order ID not found!"})
    except ValueError:
        return jsonify({"success": False, "message": "Invalid Order ID!"})

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if session.get('logged_in'):
        return redirect(url_for('admin_dashboard'))
        
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'Yash1234':
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Invalid Username or Password!'
            
    return render_template('admin.html', show_login=True, error=error)

@app.route('/admin-dashboard')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    edit_id = request.args.get('edit_id', type=int)
    edit_item = None
    if edit_id:
        edit_item = next((item for item in menu_database if item['id'] == edit_id), None)

    return render_template('admin.html', show_login=False, orders=orders_database, menu=menu_database, edit_item=edit_item)

@app.route('/add_menu_item', methods=['POST'])
def add_menu_item():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    name = request.form.get('item_name')
    price = request.form.get('item_price')
    weight = request.form.get('item_weight')
    image = request.form.get('item_image')
    
    if not image:
        image = "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500&auto=format&fit=crop&q=60"
        
    new_item_id = max((m['id'] for m in menu_database), default=0) + 1
    
    menu_database.append({
        "id": new_item_id,
        "name": name,
        "price": price,
        "weight": weight,
        "image": image
    })
    return redirect(url_for('admin_dashboard'))

@app.route('/update_menu_item/<int:item_id>', methods=['POST'])
def update_menu_item(item_id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    name = request.form.get('item_name')
    price = request.form.get('item_price')
    weight = request.form.get('item_weight')
    image = request.form.get('item_image')
    
    for item in menu_database:
        if item['id'] == item_id:
            item['name'] = name
            item['price'] = price
            item['weight'] = weight
            if image:
                item['image'] = image
            break
            
    return redirect(url_for('admin_dashboard'))

@app.route('/remove_menu_item/<int:item_id>')
def remove_menu_item(item_id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    global menu_database
    menu_database = [item for item in menu_database if item['id'] != item_id]
    return redirect(url_for('admin_dashboard'))

@app.route('/update_status/<int:order_id>/<status>')
def update_status(order_id, status):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    status_map = {
        'preparing': 'Preparing 👨‍🍳',
        'ready': 'Ready for Delivery 📦',
        'delivered': 'Delivered ✅',
        'declined': 'Declined ❌'
    }
    
    for order in orders_database:
        if order['id'] == order_id:
            order['status'] = status_map.get(status, 'Pending')
            
    return redirect(url_for('admin_dashboard'))

@app.route('/clear_orders')
def clear_orders():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    orders_database.clear()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin-logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)