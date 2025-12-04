import os
from flask import Flask
from dotenv import load_dotenv
from app import db, Doctor, Pharmacist, Patient

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    try:
        # Test connection
        print("Testing database connection...")
        print(f"Database URI: {os.getenv('DATABASE_URI')}")
        
        # Try to query doctors
        doctors = Doctor.query.all()
        print(f"✅ Found {len(doctors)} doctors:")
        for doc in doctors:
            print(f"  - {doc.name}")
        
        # Try to query patients
        patients = Patient.query.all()
        print(f"✅ Found {len(patients)} patients:")
        for pat in patients[:3]:
            print(f"  - {pat.name}")
            
        # Try to query pharmacists
        pharmacists = Pharmacist.query.all()
        print(f"✅ Found {len(pharmacists)} pharmacists:")
        for pharm in pharmacists[:3]:
            print(f"  - {pharm.name}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()