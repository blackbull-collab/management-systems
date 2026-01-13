from flask import Flask, render_template

app = Flask(__name__)

# Home Page
@app.route("/")
def home():
    return render_template("index.html")

# Products Page
@app.route("/products")
def products():
    return render_template("products.html")

# Suppliers Page
@app.route("/categories")
def suppliers():
    return render_template("categories.html")

# About Page
@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug=True)
