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
mav = None

def connect_to_mavlink():
    global mavlink_socket, mav
    retries = 3
    while retries > 0:
        try:
            mavlink_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            mavlink_socket.connect((MAVLINK_TCP_SERVER_IP, MAVLINK_TCP_SERVER_PORT))
            print("Connected to MAVLink TCP server")
            mav = mavutil.mavlink.MAVLink(mavlink_socket)
            return
        except Exception as e:
            print(f"Error connecting to MAVLink TCP server: {e}. Retrying in 5 seconds...")
            time.sleep(5)
            retries -= 1
    print("Failed to connect to MAVLink TCP server after multiple retries.")

def mavlink_receiver():
    global mavlink_socket, mav
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
                    if mav:
                        msg = mav.decode(bytearray(data))
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

def arm_disarm(arm):
    # Send MAVLink message to arm/disarm the drone
    global mavlink_socket, mav
    if mavlink_socket:
        # Create the MAVLink message
        msg = mav.command_long_encode(
            1,  # System ID
            1,  # Component ID
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,  # Command ID
            0,  # Confirmation
            arm,  # param1 (1 to arm, 0 to disarm)
            0,  # param2 (all other params are 0)
            0, 0, 0, 0, 0  # params 3-7
        )
        # Send the message
        mavlink_socket.send(msg.pack())

def takeoff():
    # Send MAVLink message to initiate takeoff
    global mavlink_socket, mav
    if mavlink_socket:
        # Create the MAVLink message
        msg = mav.command_takeoff_encode(
            1,  # System ID
            1,  # Component ID
            0,  # Confirmation
            0,  # param1 (minimum pitch)
            0,  # param2 (empty)
            0,  # param3 (empty)
            0,  # param4 (yaw)
            0,  # latitude
            0,  # longitude
            10  # altitude
        )
        # Send the message
        mavlink_socket.send(msg.pack())

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

@socketio.on('command')
def handle_command(data):
    print(f"Received command: {data}")
    if data['command'] == 'arm':
        print("Arming...")
        arm_disarm(1)
    elif data['command'] == 'disarm':
        print("Disarming...")
        arm_disarm(0)
    elif data['command'] == 'takeoff':
        print("Taking off...")
        takeoff()
    elif data['command'] == 'land':
        print("Landing...")
        # TODO: Implement landing logic
    elif data['command'] == 'rtl':
        print("Returning to launch...")
        # TODO: Implement RTL logic
    elif data['command'] == 'set_mode':
        mode = data['mode']
        print(f"Setting mode to {mode}...")
        # TODO: Implement set mode logic
    elif data['command'] == 'go_to':
        lat = data['lat']
        lon = data['lon']
        print(f"Going to latitude: {lat}, longitude: {lon}...")
        # TODO: Implement go to logic

if __name__ == '__main__':
    connect_to_mavlink()
    mavlink_thread = threading.Thread(target=mavlink_receiver)
    mavlink_thread.daemon = True
    mavlink_thread.start()
    socketio.run(app, debug=True, host='0.0.0.0')
