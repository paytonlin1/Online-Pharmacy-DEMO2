from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date
import os
from dotenv import load_dotenv
from reset import reset_bp
from extensions import db

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.register_blueprint(reset_bp)

db.init_app(app)

# DB Models
class Doctor(db.Model):
    __tablename__ = 'doctor'
    __tableargs__ = {'schema': 'pharmacy_testing'};
    doctor_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    dob = db.Column(db.Date)
    
    # Relationships
    patients = db.relationship('Patient', backref='doctor', lazy=True)
    prescriptions = db.relationship('Prescription', backref='doctor', lazy=True)

class Pharmacist(db.Model):
    __tablename__ = 'pharmacist'
    __tableargs__ = {'schema': 'pharmacy_testing'};
    pharmacist_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    dob = db.Column(db.Date)
    
    # Relationships
    orders = db.relationship('Order', backref='pharmacist', lazy=True)

class Patient(db.Model):
    __tablename__ = 'Patient'
    __tableargs__ = {'schema': 'pharmacy_testing'};
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
    __tableargs__ = {'schema': 'pharmacy_testing'};
    patient_id = db.Column(db.Integer, db.ForeignKey('Patient.patient_id'), primary_key=True)
    allergies = db.Column(db.String(200))
    family_history = db.Column(db.String(200))
    notes = db.Column(db.String(200))

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    __tableargs__ = {'schema': 'pharmacy_testing'};
    prescript_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('Patient.patient_id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.doctor_id'))
    drug_id = db.Column(db.Integer, db.ForeignKey('drug.drug_id'))
    dosage = db.Column(db.Integer)
    
    # Relationships
    drug = db.relationship('Drug', backref='prescriptions', lazy=True)
    orders = db.relationship('Order', backref='prescription', lazy=True)

class Drug(db.Model):
    __tablename__ = 'drug'
    __tableargs__ = {'schema': 'pharmacy_testing'};
    drug_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    common_ailment = db.Column(db.String(200))

class Pharmacy(db.Model):
    __tablename__ = 'pharmacy'
    __tableargs__ = {'schema': 'pharmacy_testing'};
    pharmacy_id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(100))
    name = db.Column(db.String(100))
    
    # Relationships
    orders = db.relationship('Order', backref='pharmacy', lazy=True)

class Order(db.Model):
    __tablename__ = 'orders'
    __tableargs__ = {'schema': 'pharmacy_testing'};
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
    doctor = Doctor.query.first()  
    
    if not doctor:
            flash('No doctor found in database')
            return redirect(url_for('home'))

    # Get the doctor's patients with history
    patients = db.session.query(Patient).outerjoin(
            PatientHistory, Patient.patient_id == PatientHistory.patient_id
        ).filter(Patient.doctor_id == doctor.doctor_id).all()    
    
    # Get the doctor's prescriptions
    prescriptions = Prescription.query.filter_by(doctor_id=doctor.doctor_id).all() if doctor else []
    
    # Get pending prescriptions count
    pending_prescriptions = Prescription.query.filter_by(doctor_id=doctor.doctor_id).join(Order).filter(Order.status == 'Scheduled').count() if doctor else 0
    
    all_patients = Patient.query.all()
    all_drugs = Drug.query.all()
    return render_template('doctor.html',
                         doctor=doctor,  
                         patients=patients,  
                         prescriptions=prescriptions, 
                         pending_prescriptions=pending_prescriptions,
                         all_drugs=all_drugs,
                         all_patients=all_patients)

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
    ).outerjoin(
        PatientHistory, Patient.patient_id == PatientHistory.patient_id
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

# Routes for User Input
@app.route('/patient/balance/<string:patient_name>')
def get_patient_balance(patient_name):
    patient = Patient.query.filter_by(name=patient_name).first()
    if patient:
        return {'balance': patient.balance}
    return {'error': 'Patient not found'}, 404

@app.route('/prescriptions/<string:patient_name>')
def get_prescriptions(patient_name):
    prescriptions = db.session.query(
        Prescription.dosage,
        Drug.name,
        Drug.common_ailment
    ).join(
        Patient, Prescription.patient_id == Patient.patient_id
    ).join(
        Drug, Prescription.drug_id == Drug.drug_id
    ).filter(
        Patient.name == patient_name
    ).all()
    
    return render_template('prescriptions.html', prescriptions=prescriptions)

@app.route('/patient/history/<string:patient_name>')
def get_patient_history(patient_name):
    history = db.session.query(
        PatientHistory.allergies,
        PatientHistory.family_history,
        PatientHistory.notes
    ).join(
        Patient, PatientHistory.patient_id == Patient.patient_id
    ).filter(
        Patient.name == patient_name
    ).first()
    
    if history:
        return render_template('patient_history.html', history=history)
    return {'error': 'History not found'}, 404

@app.route('/patient/history/update/<int:patient_id>', methods=['POST'])
def update_patient_history(patient_id):
    allergies = request.form.get('allergies')
    family_history = request.form.get('family_history')
    notes = request.form.get('notes')
    
    patient = Patient.query.get_or_404(patient_id)
    
    # Get or create patient history
    history = PatientHistory.query.get(patient_id)
    if not history:
        history = PatientHistory(patient_id=patient_id)
        db.session.add(history)
    
    history.allergies = allergies
    history.family_history = family_history
    history.notes = notes
    
    db.session.commit()
    
    flash(f'Patient history for {patient.name} updated successfully!', 'success')
    return redirect(url_for('doctor_dashboard'))

@app.route('/order/process/<int:order_id>', methods=['POST'])
def process_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = 'Completed'
    
    db.session.commit()
    
    flash(f'Order #{order_id} processed successfully!', 'success')
    return redirect(url_for('pharmacist_dashboard'))

@app.route('/refill/<int:prescription_id>', methods=['POST'])
def order_refill(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    patient = Patient.query.first()  # Demo - use logged-in patient
    pharmacy = Pharmacy.query.first()  # Demo - let patient choose
    pharmacist = Pharmacist.query.first()  # Demo
    
    new_order = Order(
        request_date=date.today(),
        pharmacy_id=pharmacy.pharmacy_id if pharmacy else None,
        patient_id=patient.patient_id,
        prescript_id=prescription_id,
        pharmacist_id=pharmacist.pharmacist_id if pharmacist else None,
        status='Scheduled'
    )
    
    db.session.add(new_order)
    db.session.commit()
    
    flash('Refill order placed successfully!', 'success')
    return redirect(url_for('patient_dashboard'))

@app.route('/prescription/create', methods=['POST'])
def create_prescription():
    patient_id = request.form.get('patient_id')
    drug_id = request.form.get('drug_id')
    dosage = request.form.get('dosage')

    patient = Patient.query.filter_by(patient_id=patient_id).first()
    if not patient:
        flash('Patient not found', 'error')
        return redirect(url_for('doctor_dashboard'))
    
    drug = Drug.query.filter_by(drug_id=drug_id).first()
    if not drug:
        flash('Drug not found', 'error')
        return redirect(url_for('doctor_dashboard'))
    
    doctor = Doctor.query.first()
    if not doctor:
        flash('No doctor found', 'error')
        return redirect(url_for('doctor_dashboard'))
    
    # Create new prescription (ID auto-increments)
    new_prescription = Prescription(
        patient_id=patient.patient_id,
        doctor_id=doctor.doctor_id,
        drug_id=drug.drug_id,
        dosage=dosage,
    )
    doctor = Doctor.query.first()
    
    if not doctor:
        flash('No doctor found', 'error')
        return redirect(url_for('doctor_dashboard'))
    
    db.session.add(new_prescription)
    db.session.commit()
    
    new_order = Order(
        prescript_id=new_prescription.prescript_id,
        patient_id=patient_id,
        status="Scheduled",
        request_date=date.today()
    )

    db.session.add(new_order)
    db.session.commit()

    flash('Prescription created successfully!', 'success')
    return redirect(url_for('doctor_dashboard'))
   
if __name__ == '__main__':
    app.run(debug=True)