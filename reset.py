from flask import Flask, redirect, url_for, flash, Blueprint
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text
from extensions import db

load_dotenv()

app = Flask(__name__)
reset_bp = Blueprint('reset', __name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

engine = create_engine(os.getenv('DATABASE_URI'))

@reset_bp.route('/reset_demo', methods=['POST'])
def reset_demo():
    try:
        # Drop all tables
        db.drop_all()

        # Recreate tables and insert data
        with open('insert_create.sql', 'r') as f:
            sql_commands = f.read()

        with engine.begin() as conn: 
            for cmd in sql_commands.split(';'):
                cmd = cmd.strip()
                if cmd:  # skip empty commands
                    conn.execute(text(cmd))

        flash("Demo database has been reset!", "success")
    except Exception as e:
        flash(f"Error resetting demo database: {str(e)}", "danger")

    return redirect(url_for('home'))
