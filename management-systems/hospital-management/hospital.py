from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hospital.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -------------------- MODELS --------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(50))
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(200))

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    department = db.Column(db.String(100))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"))
    patient_name = db.Column(db.String(100))
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    purpose = db.Column(db.String(100))
    status = db.Column(db.String(50), default="Scheduled")

    doctor = db.relationship("Doctor", backref=db.backref("appointments", lazy=True))

# -------------------- ROUTES --------------------
@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form["full_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        role = request.form["role"]
        username = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            return render_template("register.html", error="Username already exists!")

        new_user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            role=role,
            username=username,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session["user"] = user.username
            session["role"] = user.role
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    doctors = Doctor.query.all()
    appointments = Appointment.query.all()
    users = User.query.all()
    return render_template("dashboard.html", doctors=doctors, appointments=appointments, users=users)

@app.route("/book_appointment", methods=["POST"])
def book_appointment():
    doctor_id = request.form["doctor_id"]
    patient_name = request.form["patient_name"]
    date = request.form["date"]
    time = request.form["time"]
    purpose = request.form["purpose"]

    new_appointment = Appointment(
        doctor_id=doctor_id,
        patient_name=patient_name,
        date=date,
        time=time,
        purpose=purpose,
    )
    db.session.add(new_appointment)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -------------------- INIT DATA --------------------
with app.app_context():
    db.create_all()
    if Doctor.query.count() == 0:
        sample_doctors = [
            Doctor(name="Dr. Sarah Johnson", specialization="Cardiology", department="Heart Center"),
            Doctor(name="Dr. Michael Chen", specialization="Neurology", department="Brain & Spine Center"),
            Doctor(name="Dr. Emily Rodríguez", specialization="Pediatrics", department="Children’s Wing"),
            Doctor(name="Dr. Robert Kim", specialization="Orthopedics", department="Bone & Joint Center"),
            Doctor(name="Dr. Amanda Foster", specialization="Dermatology", department="Skin Care Center"),
        ]
        db.session.add_all(sample_doctors)
        db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)
