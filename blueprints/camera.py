# blueprints/camera.py
# blueprints/camera.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import Camera, Hall
from extensions import db

# ... rest of the file remains the same ...
camera_bp = Blueprint('camera', __name__)

@camera_bp.route('/add_camera', methods=['GET', 'POST'])
def add_camera():
    try:
        if request.method == 'POST':
            name = request.form['name']
            stream_url = request.form['stream_url']
            hall_id = request.form['hall_id']
            new_camera = Camera(name=name, stream_url=stream_url, hall_id=hall_id)
            db.session.add(new_camera)
            db.session.commit()
            flash('Camera added successfully', 'success')
            return redirect(url_for('dashboard.view_hall', hall_id=hall_id))
        
        halls = Hall.query.all()
        return render_template('add_camera.html', halls=halls)
    except Exception as e:
        current_app.logger.error(f"Error in add_camera: {e}")
        flash('An error occurred while adding the camera', 'error')
        return redirect(url_for('dashboard.view_halls'))

@camera_bp.route('/add_hall', methods=['GET', 'POST'])
def add_hall():
    try:
        if request.method == 'POST':
            name = request.form['name']
            new_hall = Hall(name=name)
            db.session.add(new_hall)
            db.session.commit()
            flash('Hall added successfully', 'success')
            return redirect(url_for('dashboard.view_halls'))
        
        return render_template('add_hall.html')
    except Exception as e:
        current_app.logger.error(f"Error in add_hall: {e}")
        flash('An error occurred while adding the hall', 'error')
        return redirect(url_for('dashboard.view_halls'))