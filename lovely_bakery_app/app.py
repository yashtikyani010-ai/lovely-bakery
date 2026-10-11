import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'lovely_bakery_secret_key_stark'

DB_FILE = 'database.json'

default_data = {
    "menu": [
        {
            "id": 1,
            "name": "Kids Super Fun Cake",
            "price": "699",
            "weight": "1 Pound",
            "age_group": "1-10",
            "image": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500&auto=format&fit=crop&q=60"
        }
    ],
    "orders": []
}

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return default_data
    return default_data

def save_data(data):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Error saving data:", e)

@app.route('/')
def index():
    data = load_data()
    selected_age = request.args.get('age_group', 'All')
    
    if selected_age and selected_age != 'All':
        filtered_menu = [item for item in data['menu'] if item.get('age_group') == selected_age]
    else:
        filtered_menu = data['menu']

    age_groups = ["All", "1-10", "10-20", "20-30", "30-40", "40-50", "50-60", "60-70"]
    return render_template('index.html', menu=filtered_menu, age_groups=age_groups, current_age=selected_age)

@app.route('/place_order', methods=['POST'])
def place_order():
    data = load_data()
    name = request.form.get('customer_name')
    phone = request.form.get('customer_phone')
    item = request.form.get('cake_item')
    quantity = request.form.get('quantity')
    
    # 2 घंटे बाद का समय कैलकुलेट करना
    now = datetime.now()
    pickup_time = (now + timedelta(hours=2)).strftime('%I:%M %p, %d %b')
    
    new_id = max((o['id'] for o in data['orders']), default=0) + 1

    new_order = {
        "id": new_id,
        "name": name,
        "phone": phone,
        "item": item,
        "quantity": int(quantity),
        "location": "Store Pickup (No Home Delivery)",
        "pickup_time": pickup_time,
        "status": "Pending"
    }
    data['orders'].append(new_order)
    save_data(data)
    return jsonify({"success": True, "order_id": new_id, "pickup_time": pickup_time, "message": "Order placed successfully!"})

@app.route('/track_order', methods=['POST'])
def track_order():
    data = load_data()
    try:
        order_id = int(request.form.get('order_id'))
        order = next((o for o in data['orders'] if o['id'] == order_id), None)
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
    
    data = load_data()
    edit_id = request.args.get('edit_id', type=int)
    edit_item = None
    if edit_id:
        edit_item = next((item for item in data['menu'] if item['id'] == edit_id), None)

    age_groups = ["1-10", "10-20", "20-30", "30-40", "40-50", "50-60", "60-70"]
    return render_template('admin.html', show_login=False, orders=data['orders'], menu=data['menu'], edit_item=edit_item, age_groups=age_groups)

@app.route('/add_menu_item', methods=['POST'])
def add_menu_item():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    data = load_data()
    name = request.form.get('item_name')
    price = request.form.get('item_price')
    weight = request.form.get('item_weight')
    age_group = request.form.get('age_group')
    image = request.form.get('item_image')
    
    if not image:
        image = "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500&auto=format&fit=crop&q=60"
        
    new_item_id = max((m['id'] for m in data['menu']), default=0) + 1
    
    data['menu'].append({
        "id": new_item_id,
        "name": name,
        "price": price,
        "weight": weight,
        "age_group": age_group,
        "image": image
    })
    save_data(data)
    return redirect(url_for('admin_dashboard'))

@app.route('/update_menu_item/<int:item_id>', methods=['POST'])
def update_menu_item(item_id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    data = load_data()
    name = request.form.get('item_name')
    price = request.form.get('item_price')
    weight = request.form.get('item_weight')
    age_group = request.form.get('age_group')
    image = request.form.get('item_image')
    
    for item in data['menu']:
        if item['id'] == item_id:
            item['name'] = name
            item['price'] = price
            item['weight'] = weight
            item['age_group'] = age_group
            if image:
                item['image'] = image
            break
            
    save_data(data)
    return redirect(url_for('admin_dashboard'))

@app.route('/remove_menu_item/<int:item_id>')
def remove_menu_item(item_id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    data = load_data()
    data['menu'] = [item for item in data['menu'] if item['id'] != item_id]
    save_data(data)
    return redirect(url_for('admin_dashboard'))

@app.route('/update_status/<int:order_id>/<status>')
def update_status(order_id, status):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    data = load_data()
    status_map = {
        'preparing': 'Preparing 👨‍🍳',
        'ready': 'Ready for Pickup 📦',
        'delivered': 'Picked Up / Completed ✅',
        'declined': 'Declined ❌'
    }
    
    for order in data['orders']:
        if order['id'] == order_id:
            order['status'] = status_map.get(status, 'Pending')
            
    save_data(data)
    return redirect(url_for('admin_dashboard'))

@app.route('/clear_orders')
def clear_orders():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    data = load_data()
    data['orders'].clear()
    save_data(data)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin-logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
