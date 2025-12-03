from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/pharmacy_testing'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# DB Models
class Doctor(db.Model):
    __tablename__ = 'doctor'
    doctor_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    dob = db.Column(db.Date)
    
    # Relationships
    patients = db.relationship('Patient', backref='doctor', lazy=True)
    prescriptions = db.relationship('Prescription', backref='doctor', lazy=True)

class Pharmacist(db.Model):
    __tablename__ = 'pharmacist'
    pharmacist_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    dob = db.Column(db.Date)
    
    # Relationships
    orders = db.relationship('Order', backref='pharmacist', lazy=True)

class Patient(db.Model):
    __tablename__ = 'Patient'
    patient_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    dob = db.Column(db.Date)
    balance = db.Column(db.Float)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.doctor_id'))
    primary_address = db.Column(db.String(100))
    
    # Relationships
    history = db.relationship('PatientHistory', backref='patient', uselist=False, lazy=True)
    prescriptions = db.relationship('Prescription', backref='patient', lazy=True)
    orders = db.relationship('Order', backref='patient', lazy=True)

class PatientHistory(db.Model):
    __tablename__ = 'PatientHistory'
    patient_id = db.Column(db.Integer, db.ForeignKey('Patient.patient_id'), primary_key=True)
    allergies = db.Column(db.String(200))
    family_history = db.Column(db.String(200))
    notes = db.Column(db.String(200))

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    prescript_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('Patient.patient_id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.doctor_id'))
    price = db.Column(db.Float)
    drug_id = db.Column(db.Integer, db.ForeignKey('drug.drug_id'))
    dosage = db.Column(db.Integer)
    
    # Relationships
    drug = db.relationship('Drug', backref='prescriptions', lazy=True)
    orders = db.relationship('Order', backref='prescription', lazy=True)

class Drug(db.Model):
    __tablename__ = 'drug'
    drug_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    common_ailment = db.Column(db.String(200))

class Pharmacy(db.Model):
    __tablename__ = 'pharmacy'
    pharmacy_id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(100))
    name = db.Column(db.String(100))
    
    # Relationships
    orders = db.relationship('Order', backref='pharmacy', lazy=True)

class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True)
    request_date = db.Column(db.Date)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacy.pharmacy_id'))
    patient_id = db.Column(db.Integer, db.ForeignKey('Patient.patient_id'))
    prescript_id = db.Column(db.Integer, db.ForeignKey('prescriptions.prescript_id'))
    pharmacist_id = db.Column(db.Integer, db.ForeignKey('pharmacist.pharmacist_id'))
    status = db.Column(db.Enum('Cancelled', 'Scheduled', 'Completed'))

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/doctor')
def doctor_dashboard():
    # Get statistics
    total_patients = Patient.query.count()
    pending_prescriptions = Prescription.query.join(Order).filter(Order.status == 'Scheduled').count()
    prescriptions_this_month = Prescription.query.filter(
        db.func.month(Order.request_date) == datetime.now().month
    ).join(Order).count()
    
    # Get recent prescriptions with patient and drug info
    recent_prescriptions = db.session.query(
        Prescription, Patient, Drug, Order
    ).join(
        Patient, Prescription.patient_id == Patient.patient_id
    ).join(
        Drug, Prescription.drug_id == Drug.drug_id
    ).outerjoin(
        Order, Prescription.prescript_id == Order.prescript_id
    ).order_by(
        Order.request_date.desc()
    ).limit(10).all()
    
    # Get today's appointments (scheduled orders)
    today_appointments = db.session.query(
        Patient, Order
    ).join(
        Order, Patient.patient_id == Order.patient_id
    ).filter(
        Order.request_date == date.today(),
        Order.status == 'Scheduled'
    ).all()
    
    return render_template('doctor.html',
                         total_patients=total_patients,
                         pending_prescriptions=pending_prescriptions,
                         prescriptions_this_month=prescriptions_this_month,
                         recent_prescriptions=recent_prescriptions,
                         today_appointments=today_appointments)

@app.route('/patient')
def patient_dashboard():
    # For demo purposes, using a dummy patient ID
    patient_id = 1
    
    # Get patient info
    patient = Patient.query.get(patient_id)
    
    # Get statistics
    active_prescriptions = Prescription.query.filter_by(patient_id=patient_id).count()
    pending_orders = Order.query.filter_by(patient_id=patient_id, status='Scheduled').count()
    completed_orders = Order.query.filter_by(patient_id=patient_id, status='Completed').count()
    
    # Get active medications (prescriptions with details)
    active_medications = db.session.query(
        Prescription, Drug, Doctor
    ).join(
        Drug, Prescription.drug_id == Drug.drug_id
    ).join(
        Doctor, Prescription.doctor_id == Doctor.doctor_id
    ).filter(
        Prescription.patient_id == patient_id
    ).all()
    
    # Get recent orders with details
    recent_orders = db.session.query(
        Order, Prescription, Drug
    ).join(
        Prescription, Order.prescript_id == Prescription.prescript_id
    ).join(
        Drug, Prescription.drug_id == Drug.drug_id
    ).filter(
        Order.patient_id == patient_id
    ).order_by(
        Order.request_date.desc()
    ).limit(5).all()
    
    # Get upcoming refills (scheduled orders)
    upcoming_refills = db.session.query(
        Order, Prescription, Drug
    ).join(
        Prescription, Order.prescript_id == Prescription.prescript_id
    ).join(
        Drug, Prescription.drug_id == Drug.drug_id
    ).filter(
        Order.patient_id == patient_id,
        Order.status == 'Scheduled',
        Order.request_date >= date.today()
    ).order_by(
        Order.request_date
    ).all()
    
    return render_template('patient.html',
                         patient=patient,
                         active_prescriptions=active_prescriptions,
                         pending_orders=pending_orders,
                         completed_orders=completed_orders,
                         active_medications=active_medications,
                         recent_orders=recent_orders,
                         upcoming_refills=upcoming_refills)

@app.route('/pharmacist')
def pharmacist_dashboard():
    # Get statistics
    pending_orders = Order.query.filter_by(status='Scheduled').count()
    completed_today = Order.query.filter(
        Order.status == 'Completed',
        Order.request_date == date.today()
    ).count()
    
    # Get prescription queue (scheduled orders)
    prescription_queue = db.session.query(
        Order, Patient, Prescription, Drug, Doctor
    ).join(
        Patient, Order.patient_id == Patient.patient_id
    ).join(
        Prescription, Order.prescript_id == Prescription.prescript_id
    ).join(
        Drug, Prescription.drug_id == Drug.drug_id
    ).join(
        Doctor, Prescription.doctor_id == Doctor.doctor_id
    ).filter(
        Order.status == 'Scheduled'
    ).order_by(
        Order.request_date
    ).limit(10).all()
    
    # Get all drugs for inventory display 
    all_drugs = Drug.query.all()
    
    return render_template('pharmacist.html',
                         pending_orders=pending_orders,
                         completed_today=completed_today,
                         prescription_queue=prescription_queue,
                         all_drugs=all_drugs)


@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized.')

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run()