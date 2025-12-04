# Online Pharmacy [DEMO]
### Created by: Nolan Le, Jeremy Matloub, Payton Lin
* For University of Pittsburgh - INFSCI 1500 FALL 2025

## Description:
* The following demo is our implementation of an online pharmacy. This is a demo version and does not have full functionality. The main purpose is to model proper data handling via a MySQL database.

## Development Stack

* **FRONTEND**: Bootstrap.js + JavaScript
* **BACKEND**: Python + Flask
* **DATABASE**: MySQL
* **PACKAGES**: SQLAlchemy

## Setup

```bash
git clone https://github.com/paytonlin1/Online-Pharmacy-DEMO2.git

# Initilizes DB and creates all tables with dummy data inserted 
python reset.py 

# Install dependencies
python install -r requirements.txt

# Run Flask app
python app.py
```

## Assumptions
* Users only use the dashboard that corresponds to their role.
* All doctors and pharmacists in the system are accordingly verified employees
* Each patient is associated with exactly one primary doctor.
* Each patient has one medical history record.
* A doctor may oversee many patients and issue many prescriptions.
* A pharmacist may schedule many pickups.
* Each order corresponds to exactly one prescription.s
* All user inputs are via drop-down menus, preventing malformed submissions.

## Improvements
* Integrating real-world drug prices
* Insurance and billing support
* Inventory tracking and management
* Built-in pickup scheduling
* Automated allergy and drug interaction alerts