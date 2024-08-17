# blueprints/dashboard.py
from flask import Blueprint, render_template, Response, jsonify, current_app
from models import Camera, Hall, PeopleCount
from extensions import db
import cv2
from people_counter import PeopleCounter
import threading
import queue

dashboard_bp = Blueprint('dashboard', __name__)
people_counters = {}
frame_queues = {}
processing_threads = {}

def process_frames(app, camera_id, frame_queue, counter):
    with app.app_context():
        while True:
            frame = frame_queue.get()
            if frame is None:
                break
            processed_frame, in_count, out_count = counter.detect_and_track(frame)
            new_count = PeopleCount(camera_id=camera_id, count=in_count - out_count, in_count=in_count, out_count=out_count)
            db.session.add(new_count)
            db.session.commit()

def generate_frames(app, camera):
    with app.app_context():
        if camera.id not in people_counters:
            people_counters[camera.id] = PeopleCounter()
        
        counter = people_counters[camera.id]
        
        cap = cv2.VideoCapture(camera.stream_url)
        
        if not cap.isOpened():
            raise Exception(f"Cannot open camera stream: {camera.stream_url}")

        if camera.id not in frame_queues:
            frame_queues[camera.id] = queue.Queue()
            processing_threads[camera.id] = threading.Thread(
                target=process_frames,
                args=(app, camera.id, frame_queues[camera.id], counter)
            )
            processing_threads[camera.id].start()

        try:
            while True:
                success, frame = cap.read()
                if not success:
                    break
                frame_queues[camera.id].put(frame)
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        finally:
            cap.release()
            frame_queues[camera.id].put(None)
            processing_threads[camera.id].join()

@dashboard_bp.route('/')
def view_halls():
    halls = Hall.query.all()
    return render_template('view_halls.html', halls=halls)

@dashboard_bp.route('/hall/<int:hall_id>')
def view_hall(hall_id):
    hall = Hall.query.get_or_404(hall_id)
    return render_template('view_hall.html', hall=hall)

@dashboard_bp.route('/camera/<int:camera_id>')
def view_camera(camera_id):
    camera = Camera.query.get_or_404(camera_id)
    return render_template('view_camera.html', camera=camera)

@dashboard_bp.route('/video_feed/<int:camera_id>')
def video_feed(camera_id):
    camera = Camera.query.get_or_404(camera_id)
    return Response(generate_frames(current_app._get_current_object(), camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@dashboard_bp.route('/hall_counts/<int:hall_id>')
def hall_counts(hall_id):
    hall = Hall.query.get_or_404(hall_id)
    total_in = sum(camera.counts[-1].in_count if camera.counts else 0 for camera in hall.cameras)
    total_out = sum(camera.counts[-1].out_count if camera.counts else 0 for camera in hall.cameras)
    current_count = total_in - total_out
    return jsonify({'in': total_in, 'out': total_out, 'current': current_count})

@dashboard_bp.route('/camera_counts/<int:camera_id>')
def camera_counts(camera_id):
    camera = Camera.query.get_or_404(camera_id)
    latest_count = camera.counts[-1] if camera.counts else None
    if latest_count:
        return jsonify({
            'in': latest_count.in_count,
            'out': latest_count.out_count,
            'current': latest_count.count
        })
    else:
        return jsonify({'in': 0, 'out': 0, 'current': 0})
@dashboard_bp.route('/search', methods=['GET', 'POST'])
def search():
    try:
        if request.method == 'POST':
            start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
            end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
            hall_id = request.form['hall_id']
            
            hall = Hall.query.get_or_404(hall_id)
            counts = PeopleCount.query.join(Camera).filter(
                Camera.hall_id == hall_id,
                PeopleCount.timestamp.between(start_time, end_time)
            ).all()
            
            total_in = sum(count.in_count for count in counts)
            total_out = sum(count.out_count for count in counts)
            current_count = total_in - total_out
            
            return render_template('search_results.html', hall=hall, counts=counts, 
                                   total_in=total_in, total_out=total_out, current_count=current_count)
        
        halls = Hall.query.all()
        return render_template('search.html', halls=halls)
    except Exception as e:
        current_app.logger.error(f"Error in search: {e}")
        return render_template('error.html', error="An error occurred while processing your request"), 500