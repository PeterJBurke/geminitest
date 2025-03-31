var socket = io('http://localhost:5000'); // Replace with your backend URL
var map = L.map('map').setView([0, 0], 2); // Default view

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

var droneMarker = L.marker([0, 0]).addTo(map);
var homeMarker = L.marker([0, 0]).addTo(map);

socket.on('connect', function() {
    console.log('Connected to backend');
    document.getElementById('connectionStatus').innerText = 'Connected';
});

socket.on('disconnect', function() {
    console.log('Disconnected from backend');
    document.getElementById('connectionStatus').innerText = 'Disconnected';
});

socket.on('telemetry', function(data) {
    // Update map
    droneMarker.setLatLng([data.latitude, data.longitude]);
    map.panTo([data.latitude, data.longitude]);

    // Update status box
    document.getElementById('ekfStatus').innerText = data.ekfStatus;
});

// PFD Canvas
var pfdCanvas = document.getElementById('pfdCanvas');
var pfdContext = pfdCanvas.getContext('2d');

function drawPFD() {
    // Clear canvas
    pfdContext.clearRect(0, 0, pfdCanvas.width, pfdCanvas.height);

    // Draw sky
    pfdContext.fillStyle = '#87CEEB';
    pfdContext.fillRect(0, 0, pfdCanvas.width, pfdCanvas.height / 2);

    // Draw ground
    pfdContext.fillStyle = '#8B4513';
    pfdContext.fillRect(0, pfdCanvas.height / 2, pfdCanvas.width, pfdCanvas.height / 2);

    // Draw horizon line
    pfdContext.strokeStyle = '#000';
    pfdContext.lineWidth = 2;
    pfdContext.beginPath();
    pfdContext.moveTo(0, pfdCanvas.height / 2);
    pfdContext.lineTo(pfdCanvas.width, pfdCanvas.height / 2);
    pfdContext.stroke();
}

drawPFD();

// Controls
document.getElementById('armButton').addEventListener('click', function() {
    socket.emit('command', {command: 'arm'});
});

document.getElementById('disarmButton').addEventListener('click', function() {
    socket.emit('command', {command: 'disarm'});
});

document.getElementById('takeoffButton').addEventListener('click', function() {
    socket.emit('command', {command: 'takeoff'});
});

document.getElementById('landButton').addEventListener('click', function() {
    socket.emit('command', {command: 'land'});
});

document.getElementById('rtlButton').addEventListener('click', function() {
    socket.emit('command', {command: 'rtl'});
});

document.getElementById('modeSelect').addEventListener('change', function() {
    socket.emit('command', {command: 'set_mode', mode: this.value});
});

document.getElementById('goToButton').addEventListener('click', function() {
    var lat = document.getElementById('latInput').value;
    var lon = document.getElementById('lonInput').value;
    socket.emit('command', {command: 'go_to', lat: lat, lon: lon});
});

document.getElementById('clearGoToButton').addEventListener('click', function() {
    document.getElementById('latInput').value = '';
    document.getElementById('lonInput').value = '';
});
