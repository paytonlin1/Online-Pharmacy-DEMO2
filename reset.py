from flask import Flask, redirect, url_for, flash, Blueprint
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from sqlalchemy import text
from extensions import db

load_dotenv()

reset_bp = Blueprint('reset', __name__)

@reset_bp.route('/reset_demo', methods=['POST'])
def reset_demo():
    try:
        # Read the SQL file
        with open('insert_create.sql', 'r') as f:
            sql_commands = f.read()

        with db.engine.begin() as conn:
            # Disable foreign key checks
            conn.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
            
            # Drop all tables if they exist
            tables_to_drop = ['orders', 'prescriptions', 'patienthistory', 'user', 
                            'patient', 'pharmacy', 'drug', 'pharmacist', 'doctor']
            for table in tables_to_drop:
                conn.execute(text(f'DROP TABLE IF EXISTS pharmacy_testing.{table}'))
            
            # Re-enable foreign key checks
            conn.execute(text('SET FOREIGN_KEY_CHECKS = 1'))
            
            # Execute all CREATE and INSERT commands from your SQL file
            for cmd in sql_commands.split(';'):
                cmd = cmd.strip()
                if cmd and not cmd.upper().startswith('USE'):  # Skip USE statement
                    try:
                        conn.execute(text(cmd))
                    except Exception as e:
                        print(f"Error executing command: {cmd[:50]}...")
                        print(f"Error: {e}")
        
        # IMPORTANT: Tell SQLAlchemy to refresh its metadata
        db.reflect()
        
        flash("Demo database has been reset!", "success")
    except Exception as e:
        flash(f"Error resetting demo database: {str(e)}", "danger")
        print(f"Full error: {e}")

    return redirect(url_for('home'))