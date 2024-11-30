from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "secret_key"

# Función para inicializar la base de datos
def init_db():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    # Tabla de productos/materiales
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL
    )
    """)

    # Tabla de clientes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT
    )
    """)

    # Tabla de órdenes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        total_price REAL NOT NULL,
        order_date TEXT NOT NULL,
        FOREIGN KEY (client_id) REFERENCES clients(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)

    # Tabla de gastos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        amount REAL NOT NULL,
        expense_date TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

# Ruta principal: Tablero
@app.route("/")
def index():
    return render_template("index.html")

# Gestión de productos
@app.route("/inventory")
def inventory():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return render_template("inventory.html", products=products)

@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        quantity = request.form["quantity"]
        price = request.form["price"]

        conn = sqlite3.connect("inventory.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (name, description, quantity, price) VALUES (?, ?, ?, ?)",
                       (name, description, quantity, price))
        conn.commit()
        conn.close()

        flash("Producto agregado exitosamente")
        return redirect(url_for("inventory"))

    return render_template("add_product.html")

# Gestión de clientes
@app.route("/clients")
def clients():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients")
    clients = cursor.fetchall()
    conn.close()
    return render_template("clients.html", clients=clients)

@app.route("/add_client", methods=["GET", "POST"])
def add_client():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        email = request.form["email"]

        conn = sqlite3.connect("inventory.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO clients (name, phone, email) VALUES (?, ?, ?)",
                       (name, phone, email))
        conn.commit()
        conn.close()

        flash("Cliente agregado exitosamente")
        return redirect(url_for("clients"))

    return render_template("add_client.html")

# Gestión de órdenes
@app.route("/orders")
def orders():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("""
    SELECT orders.id, clients.name, products.name, orders.quantity, orders.total_price, orders.order_date
    FROM orders
    JOIN clients ON orders.client_id = clients.id
    JOIN products ON orders.product_id = products.id
    """)
    orders = cursor.fetchall()
    conn.close()
    return render_template("orders.html", orders=orders)

@app.route("/add_order", methods=["GET", "POST"])
def add_order():
    if request.method == "POST":
        try:
            client_id = request.form["client_id"]
            product_id = request.form["product_id"]
            quantity = int(request.form["quantity"])
            order_date = request.form["order_date"]
        except KeyError as e:
            flash(f"Falta un campo requerido: {e.args[0]}")
            return redirect(url_for("add_order"))

        conn = sqlite3.connect("inventory.db")
        cursor = conn.cursor()

        # Calcular precio total
        cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,))
        price = cursor.fetchone()
        if price is None:
            flash("Producto no encontrado.")
            return redirect(url_for("add_order"))

        total_price = price[0] * quantity

        cursor.execute("""
        INSERT INTO orders (client_id, product_id, quantity, total_price, order_date)
        VALUES (?, ?, ?, ?, ?)
        """, (client_id, product_id, quantity, total_price, order_date))
        conn.commit()
        conn.close()

        flash("Orden agregada exitosamente")
        return redirect(url_for("orders"))

    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients")
    clients = cursor.fetchall()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return render_template("add_order.html", clients=clients, products=products)

# Gestión de gastos
@app.route("/expenses")
def expenses():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()
    conn.close()
    return render_template("expenses.html", expenses=expenses)

@app.route("/add_expense", methods=["GET", "POST"])
def add_expense():
    if request.method == "POST":
        name = request.form["name"]
        amount = float(request.form["amount"])
        expense_date = request.form["expense_date"]

        # Guardar en la base de datos
        conn = sqlite3.connect("inventory.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO expenses (name, amount, expense_date) VALUES (?, ?, ?)",
                       (name, amount, expense_date))
        conn.commit()
        conn.close()

        flash("Gasto agregado exitosamente")
        return redirect(url_for("expenses"))

    return render_template("add_expense.html")

# Ruta para los informes (reports)
@app.route("/reports")
def reports():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    
    # Obtener el total de ventas y gastos
    cursor.execute("SELECT SUM(total_price) FROM orders")
    total_sales = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_expenses = cursor.fetchone()[0] or 0.0
    
    # Calcular el beneficio neto
    net_profit = total_sales - total_expenses

    conn.close()

    return render_template("reports.html", total_sales=total_sales, total_expenses=total_expenses, net_profit=net_profit)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
