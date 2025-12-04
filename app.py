from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os
from dotenv import load_dotenv


app = Flask(__name__)

load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
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
    total_patients = Patient.query.count()
    total_doctors = Doctor.query.count()
    total_prescriptions = Prescription.query.count()
    total_pharmacists = Pharmacist.query.count()
    
    return render_template('home.html',
                         total_patients=total_patients,
                         total_doctors=total_doctors,
                         total_prescriptions=total_prescriptions,
                         total_pharmacists=total_pharmacists)

@app.route('/doctor_dashboard')
def doctor_dashboard():
    # For demo purposes, get the first doctor (or use a specific doctor_id)
    doctor = Doctor.query.first()  # Add this line
    
    # Get the doctor's patients
    patients = Patient.query.filter_by(doctor_id=doctor.doctor_id).all() if doctor else []
    
    # Get the doctor's prescriptions
    prescriptions = Prescription.query.filter_by(doctor_id=doctor.doctor_id).all() if doctor else []
    
    # Get pending prescriptions count
    pending_prescriptions = Prescription.query.filter_by(doctor_id=doctor.doctor_id).join(Order).filter(Order.status == 'Scheduled').count() if doctor else 0
    
    return render_template('doctor.html',
                         doctor=doctor,  # Add this
                         patients=patients,  # Add this
                         prescriptions=prescriptions,  # Add this
                         pending_prescriptions=pending_prescriptions)

@app.route('/patient_dashboard')
def patient_dashboard():
    # For demo purposes, using first patient
    patient = Patient.query.first()
    
    if not patient:
        flash('No patient found in database')
        return redirect(url_for('home'))
    
    # Get prescriptions with drug info
    prescriptions = db.session.query(Prescription).join(
        Drug, Prescription.drug_id == Drug.drug_id
    ).filter(
        Prescription.patient_id == patient.patient_id
    ).all()
    
    # Get statistics
    active_prescriptions = len(prescriptions)
    pending_orders = Order.query.filter_by(
        patient_id=patient.patient_id, 
        status='Scheduled'
    ).count()
    completed_orders = Order.query.filter_by(
        patient_id=patient.patient_id, 
        status='Completed'
    ).count()
    
    # Get recent orders
    recent_orders = db.session.query(Order).join(
        Prescription, Order.prescript_id == Prescription.prescript_id
    ).join(
        Drug, Prescription.drug_id == Drug.drug_id
    ).filter(
        Order.patient_id == patient.patient_id
    ).order_by(Order.request_date.desc()).limit(5).all()
    
    return render_template('patient.html',
                         patient=patient,
                         prescriptions=prescriptions,
                         active_prescriptions=active_prescriptions,
                         pending_orders=pending_orders,
                         completed_orders=completed_orders,
                         recent_orders=recent_orders)

@app.route('/pharmacist_dashboard')
def pharmacist_dashboard():
    # Get a pharmacist (for demo, using first pharmacist)
    pharmacist = Pharmacist.query.first()
    
    if not pharmacist:
        flash('No pharmacist found in database')
        return redirect(url_for('home'))
    
    # Get pending orders with all related info
    pending_orders = db.session.query(Order).join(
        Patient, Order.patient_id == Patient.patient_id
    ).join(
        Prescription, Order.prescript_id == Prescription.prescript_id
    ).join(
        Drug, Prescription.drug_id == Drug.drug_id
    ).join(
        Doctor, Prescription.doctor_id == Doctor.doctor_id
    ).filter(
        Order.status == 'Scheduled'
    ).all()
    
    # Get statistics
    pending_count = len(pending_orders)
    completed_today = Order.query.filter(
        Order.status == 'Completed',
        Order.request_date == date.today()
    ).count()
    
    # Dummy data for demo
    low_stock_count = 3
    out_for_delivery = 5
    
    return render_template('pharmacist.html',
                         pharmacist=pharmacist,
                         pending_orders=pending_orders,
                         pending_count=pending_count,
                         completed_today=completed_today,
                         low_stock_count=low_stock_count,
                         out_for_delivery=out_for_delivery)

if __name__ == '__main__':
    app.run(debug=True)