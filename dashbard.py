<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DLP Monitor Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }

        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .status-bar {
            display: flex;
            gap: 20px;
            align-items: center;
            margin-top: 20px;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 20px;
            background: #f0f0f0;
            border-radius: 25px;
        }

        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #e74c3c;
            animation: pulse 2s infinite;
        }

        .status-dot.active {
            background: #2ecc71;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .control-buttons {
            display: flex;
            gap: 10px;
        }

        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }

        .btn-start {
            background: #2ecc71;
            color: white;
        }

        .btn-stop {
            background: #e74c3c;
            color: white;
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }

        .card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }

        .stat-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
        }

        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }

        .events-container {
            grid-column: 1 / -1;
        }

        .events-list {
            max-height: 500px;
            overflow-y: auto;
        }

        .event-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        .event-item.new {
            background: #fff3cd;
            border-left-color: #ffc107;
        }

        .event-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }

        .event-type {
            font-weight: bold;
            color: #667eea;
        }

        .event-timestamp {
            color: #666;
            font-size: 0.9em;
        }

        .event-details {
            font-size: 0.95em;
            color: #333;
        }

        .event-path {
            font-family: 'Courier New', monospace;
            background: white;
            padding: 5px 10px;
            border-radius: 5px;
            margin-top: 5px;
            word-break: break-all;
        }

        .label-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: 600;
            margin-left: 10px;
        }

        .label-confidential {
            background: #e74c3c;
            color: white;
        }

        .label-secret {
            background: #c0392b;
            color: white;
        }

        .label-internal {
            background: #f39c12;
            color: white;
        }

        .label-restricted {
            background: #e67e22;
            color: white;
        }

        .monitored-files-list {
            max-height: 400px;
            overflow-y: auto;
        }

        .file-item {
            background: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 8px;
            font-size: 0.9em;
        }

        .file-hash {
            font-family: 'Courier New', monospace;
            color: #666;
            font-size: 0.8em;
        }

        .alert-notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #2ecc71;
            color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
            z-index: 1000;
            animation: slideInRight 0.3s ease;
        }

        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(100px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        .alert-warning {
            background: #e74c3c;
        }

        .connection-status {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 10px 20px;
            background: white;
            border-radius: 25px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            gap: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ DLP Monitor Dashboard</h1>
            <p style="color: #666; margin-top: 10px;">Real-time Data Loss Prevention Monitoring System</p>
            
            <div class="status-bar">
                <div class="status-indicator">
                    <div class="status-dot" id="statusDot"></div>
                    <span id="statusText">Monitoring Inactive</span>
                </div>
                <div class="status-indicator">
                    <span>📁 <strong id="fileCount">0</strong> Files Monitored</span>
                </div>
                <div class="control-buttons">
                    <button class="btn btn-start" onclick="startMonitoring()">▶️ Start Monitoring</button>
                    <button class="btn btn-stop" onclick="stopMonitoring()">⏸️ Stop Monitoring</button>
                </div>
            </div>
        </div>

        <div class="dashboard-grid">
            <div class="card">
                <h2>📊 Statistics</h2>
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-number" id="totalEvents">0</div>
                        <div class="stat-label">Total Events</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number" id="todayEvents">0</div>
                        <div class="stat-label">Today's Events</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number" id="alertCount">0</div>
                        <div class="stat-label">Active Alerts</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>📂 Monitored Files</h2>
                <div class="monitored-files-list" id="monitoredFilesList">
                    <p style="color: #666;">Loading...</p>
                </div>
            </div>

            <div class="card events-container">
                <h2>🔔 Recent Events (Live Stream)</h2>
                <div class="events-list" id="eventsList">
                    <p style="color: #666;">No events yet. Monitoring will show events here in real-time.</p>
                </div>
            </div>
        </div>
    </div>

    <div class="connection-status" id="connectionStatus">
        <div class="status-dot"></div>
        <span>Connecting...</span>
    </div>

    <script>
        // Socket.IO connection
        const socket = io();
        let eventCount = 0;
        let todayEventCount = 0;

        // Connection handlers
        socket.on('connect', function() {
            console.log('Connected to DLP Monitor');
            document.getElementById('connectionStatus').innerHTML = 
                '<div class="status-dot active"></div><span>Connected</span>';
            loadInitialData();
        });

        socket.on('disconnect', function() {
            console.log('Disconnected from DLP Monitor');
            document.getElementById('connectionStatus').innerHTML = 
                '<div class="status-dot"></div><span>Disconnected</span>';
        });

        // Real-time file event handler
        socket.on('file_event', function(data) {
            console.log('File event received:', data);
            addEventToList(data, true);
            showAlert(data);
            eventCount++;
            todayEventCount++;
            updateStats();
        });

        // Load initial data
        async function loadInitialData() {
            await loadMonitoringStatus();
            await loadMonitoredFiles();
            await loadRecentEvents();
        }

        async function loadMonitoringStatus() {
            try {
                const response = await fetch('/api/monitoring/status');
                const data = await response.json();
                updateMonitoringStatus(data.active);
                document.getElementById('fileCount').textContent = data.watched_files;
            } catch (error) {
                console.error('Error loading status:', error);
            }
        }

        async function loadMonitoredFiles() {
            try {
                const response = await fetch('/api/monitored_files');
                const files = await response.json();
                
                const container = document.getElementById('monitoredFilesList');
                if (files.length === 0) {
                    container.innerHTML = '<p style="color: #666;">No files being monitored</p>';
                    return;
                }
                
                container.innerHTML = files.map(file => `
                    <div class="file-item">
                        <div><strong>${file.path || 'N/A'}</strong></div>
                        <div class="label-badge label-${file.label}">${file.label.toUpperCase()}</div>
                        <div class="file-hash">${file.sha256.substring(0, 16)}...</div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading files:', error);
            }
        }

        async function loadRecentEvents() {
            try {
                const response = await fetch('/api/events?limit=50');
                const events = await response.json();
                
                const container = document.getElementById('eventsList');
                if (events.length === 0) {
                    return;
                }
                
                container.innerHTML = '';
                events.forEach(event => addEventToList(event, false));
                
                eventCount = events.length;
                updateStats();
            } catch (error) {
                console.error('Error loading events:', error);
            }
        }

        function addEventToList(event, isNew) {
            const container = document.getElementById('eventsList');
            const timestamp = new Date(event.timestamp).toLocaleString();
            
            const eventDiv = document.createElement('div');
            eventDiv.className = 'event-item' + (isNew ? ' new' : '');
            eventDiv.innerHTML = `
                <div class="event-header">
                    <div>
                        <span class="event-type">${event.event_type}</span>
                        <span class="label-badge label-${event.label}">${event.label.toUpperCase()}</span>
                    </div>
                    <span class="event-timestamp">${timestamp}</span>
                </div>
                <div class="event-details">
                    <div>👤 User: <strong>${event.user}</strong></div>
                    <div class="event-path">📄 ${event.file_path}</div>
                    ${event.new_path ? `<div class="event-path">➡️ ${event.new_path}</div>` : ''}
                    ${event.details ? `<div style="margin-top: 5px; color: #666;">${event.details}</div>` : ''}
                </div>
            `;
            
            container.insertBefore(eventDiv, container.firstChild);
            
            // Remove animation class after animation completes
            if (isNew) {
                setTimeout(() => eventDiv.classList.remove('new'), 3000);
            }
            
            // Keep only last 50 events in DOM
            while (container.children.length > 50) {
                container.removeChild(container.lastChild);
            }
        }

        function showAlert(event) {
            const alert = document.createElement('div');
            alert.className = 'alert-notification alert-warning';
            alert.innerHTML = `
                <div style="font-weight: bold; margin-bottom: 5px;">⚠️ ${event.event_type}</div>
                <div style="font-size: 0.9em;">${event.file_path.split('\\').pop()}</div>
                <div style="font-size: 0.85em; margin-top: 5px; opacity: 0.9;">User: ${event.user}</div>
            `;
            
            document.body.appendChild(alert);
            
            // Auto remove after 5 seconds
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            }, 5000);
            
            // Play notification sound (optional)
            try {
                const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG');
                audio.play();
            } catch (e) {}
        }

        function updateStats() {
            document.getElementById('totalEvents').textContent = eventCount;
            document.getElementById('todayEvents').textContent = todayEventCount;
            document.getElementById('alertCount').textContent = eventCount;
        }

        async function startMonitoring() {
            try {
                const response = await fetch('/api/monitoring/start', { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    updateMonitoringStatus(true);
                    showAlert({ event_type: 'SYSTEM', file_path: 'Monitoring Started', user: 'System' });
                }
            } catch (error) {
                console.error('Error starting monitoring:', error);
            }
        }

        async function stopMonitoring() {
            try {
                const response = await fetch('/api/monitoring/stop', { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    updateMonitoringStatus(false);
                }
            } catch (error) {
                console.error('Error stopping monitoring:', error);
            }
        }

        function updateMonitoringStatus(isActive) {
            const dot = document.getElementById('statusDot');
            const text = document.getElementById('statusText');
            
            if (isActive) {
                dot.classList.add('active');
                text.textContent = 'Monitoring Active';
            } else {
                dot.classList.remove('active');
                text.textContent = 'Monitoring Inactive';
            }
        }

        // Auto-refresh monitoring status every 5 seconds
        setInterval(loadMonitoringStatus, 5000);
    </script>
</body>
</html>
