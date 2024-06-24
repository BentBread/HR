from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import datetime
app = Flask(__name__)
app.secret_key = 'supersecretkey'
import requests

# Load data
def load_data():
    if os.path.exists('data.json'):
        with open('data.json', 'r') as file:
            return json.load(file)
    return {'users': [], 'items': []}

# Save data
def save_data(data):
    with open('data.json', 'w') as file:
        json.dump(data, file, indent=4)

# Load completed purchases
def load_purchases():
    if os.path.exists('purchases.json'):
        with open('purchases.json', 'r') as file:
            return json.load(file)
    return {'purchases': []}

# Save completed purchases
def save_purchases(purchases):
    with open('purchases.json', 'w') as file:
        json.dump(purchases, file, indent=4)

data = load_data()
purchases = load_purchases()

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('marketplace'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        for user in data['users']:
            if user['username'] == username and user['password'] == password:
                session['username'] = username
                session['nation'] = user['nation']
                session['password'] = user['password']
                return redirect(url_for('marketplace'))
        return "Invalid username or password"
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        nation = request.form['nation']
        username = request.form['username']
        password = request.form['password']
        if username and password:
            data['users'].append({'nation': nation, 'username': username, 'password': password})
            save_data(data)
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/marketplace')
def marketplace():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('marketplace.html', items=data['items'])

@app.route('/account', methods=['GET', 'POST'])
def account():
    if 'username' not in session:
        return redirect(url_for('login'))
    user_items = [item for item in data['items'] if item['username'] == session['username']]
    user_purchases = [purchase for purchase in purchases['purchases'] if purchase['buyer'] == session['username']]
    user_sales = [purchase for purchase in purchases['purchases'] if purchase['seller'] == session['username']]
    return render_template('account.html', user=session, items=user_items, purchases=user_purchases, sales=user_sales)

@app.route('/update_account', methods=['GET', 'POST'])
def update_account():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        new_nation = request.form['new_nation']
        new_username = request.form['new_username']
        for user in data['users']:
            if user['username'] == session['username']:
                user['nation'] = new_nation
                user['username'] = new_username
                session['username'] = new_username
                session['nation'] = new_nation
                save_data(data)
                break
        return redirect(url_for('account'))
    return render_template('update_account.html', user=session)

@app.route('/add_item', methods=['POST'])
def add_item():
    if 'username' not in session:
        return redirect(url_for('login'))
    item_name = request.form['item_name']
    item_prices = request.form.getlist('item_price[]')
    item_amount = int(request.form['item_amount'])
    item_nation = session['nation']
    instant = 'instant' in request.form
    instant_text = request.form['instant_text'] if instant else ''
    new_item = {
        'item_name': item_name,
        'item_price': item_prices,
        'item_nation': item_nation,
        'username': session['username'],
        'item_amount': item_amount,
        'instant': instant,
        'instant_text': instant_text
    }
    data['items'].append(new_item)
    save_data(data)
    return redirect(url_for('account'))

@app.route('/delete_item/<item_name>', methods=['POST'])
def delete_item(item_name):
    if 'username' not in session:
        return redirect(url_for('login'))
    data['items'] = [item for item in data['items'] if not (item['item_name'] == item_name and item['username'] == session['username'])]
    save_data(data)
    return redirect(url_for('account'))

@app.route('/locations')
def locations():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('locations.html')

@app.route('/about')
def about():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('about.html')


@app.route('/buy_item', methods=['POST'])
def buy_item():
    if 'username' not in session:
        return redirect(url_for('login'))
    item_name = request.form['item_name']
    amount = int(request.form['amount'])
    price = request.form['price']
    buyer = session['username']
    instant_text = ""

    # Prevent users from buying their own items
    for item in data['items']:
        if item['item_name'] == item_name and price in item['item_price']:
            if item['username'] == buyer:
                return "You cannot buy your own item."

            # Process the purchase
            print(f"User: {buyer} bought: {amount} amount: {item_name} price: {price}")
            if item['instant']:
                instant_text = item['instant_text']

            # Update item amount in data
            item['item_amount'] -= amount
            if item['item_amount'] <= 0:
                data['items'].remove(item)

            # Record the purchase
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            purchase = {
                'buyer': buyer,
                'item_name': item_name,
                'amount': amount,
                'price': price,
                'instant': item['instant'],
                'instant_text': instant_text,
                'seller': item['username'],
                'timestamp': timestamp
            }
            purchases['purchases'].append(purchase)
            save_purchases(purchases)

            # Send purchase info to Discord bot
            discord_webhook_url = "http://localhost:5001/notify_purchase"
            requests.post(discord_webhook_url, json=purchase)
            
            break
    save_data(data)
    return redirect(url_for('view_purchase', item_name=item_name, amount=amount, price=price, instant=item['instant'], instant_text=instant_text, timestamp=timestamp))


@app.route('/view_purchase')
def view_purchase():
    if 'username' not in session:
        return redirect(url_for('login'))
    item_name = request.args.get('item_name')
    amount = request.args.get('amount')
    price = request.args.get('price')
    instant = request.args.get('instant') == 'True'
    instant_text = request.args.get('instant_text')
    timestamp = request.args.get('timestamp')
    return render_template('view_purchase.html', item_name=item_name, amount=amount, price=price, instant=instant, instant_text=instant_text, timestamp=timestamp)

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    session.pop('nation', None)
    session.pop('password', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
