import gevent
from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import socket
import time
import struct
import threading
from pymavlink import mavutil

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='gevent')

MAVLINK_TCP_SERVER_IP = '192.168.1.247'
MAVLINK_TCP_SERVER_PORT = 5678

mavlink_socket = None

def connect_to_mavlink():
    global mavlink_socket
    retries = 3
    while retries > 0:
        try:
            mavlink_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            mavlink_socket.connect((MAVLINK_TCP_SERVER_IP, MAVLINK_TCP_SERVER_PORT))
            print("Connected to MAVLink TCP server")
            return
        except Exception as e:
            print(f"Error connecting to MAVLink TCP server: {e}. Retrying in 5 seconds...")
            time.sleep(5)
            retries -= 1
    print("Failed to connect to MAVLink TCP server after multiple retries.")

def mavlink_receiver():
    while True:
        try:
            if mavlink_socket:
                data = mavlink_socket.recv(4096)
                if not data:
                    print("Disconnected from MAVLink TCP server")
                    connect_to_mavlink()
                    continue

                # Parse MAVLink messages
                try:
                    msg = mavutil.mavlink.MAVLink_message.decode(data)
                    if msg:
                        if msg.get_msgId() == mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT:
                            latitude = msg.lat / 1e7
                            longitude = msg.lon / 1e7
                            print(f"Latitude: {latitude}, Longitude: {longitude}")
                            socketio.emit('telemetry', {'latitude': latitude, 'longitude': longitude, 'ekfStatus': 'OK'}) # Example EKF status
                except Exception as e:
                    print(f"Error decoding MAVLink message: {e}")

        except Exception as e:
            print(f"Error receiving MAVLink data: {e}")
            connect_to_mavlink()

@app.route('/')
def index():
    return render_template('../frontend/index.html')

@socketio.on('connect')
def test_connect():
    print('Client connected')
    emit('my response', {'data': 'Connected!'})

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    connect_to_mavlink()
    mavlink_thread = threading.Thread(target=mavlink_receiver)
    mavlink_thread.daemon = True
    mavlink_thread.start()
    socketio.run(app, debug=True, host='0.0.0.0')
