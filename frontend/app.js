const API_BASE = `${window.CONFIG.API_URL}/api`;

// DOM Elements
const btnWebcam = document.getElementById('btn-webcam');
const btnSimulate = document.getElementById('btn-simulate');
const fileInput = document.getElementById('file-input');
const webcamVideo = document.getElementById('webcam-video');
const resultImage = document.getElementById('result-image');
const placeholder = document.getElementById('feed-placeholder');
const overlay = document.getElementById('processing-overlay');
const incidentList = document.getElementById('incident-list');
const incidentCount = document.getElementById('incident-count');
const mainContainer = document.getElementById('main-container');

// State
let stream = null;
let captureInterval = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    fetchIncidents();
    connectWebSocket();
});

// WebSocket Connection
function connectWebSocket() {
    const wsUrl = `${window.CONFIG.WS_URL}/ws/alerts/`;
    const socket = new WebSocket(wsUrl);
    
    socket.onopen = () => console.log('Connected to Security Alert System (WebSockets).');
    
    socket.onmessage = (e) => {
        const data = JSON.parse(e.data);
        console.log('Real-Time Alert Received!', data);
        
        // Flash UI instantly!
        triggerRedAlert();
        
        // Refresh incidents
        fetchIncidents();
    };
    
    socket.onclose = () => {
        console.log('WebSocket closed. Retrying in 3s...');
        setTimeout(connectWebSocket, 3000);
    };
}

// Fetch Incidents from Django
async function fetchIncidents() {
    try {
        const response = await fetch(`${API_BASE}/incidents/`);
        const data = await response.json();
        renderIncidents(data);
    } catch (err) {
        console.error('Error fetching incidents:', err);
        incidentList.innerHTML = `<div class="text-center text-red-500 mt-4 text-sm"><i class="ri-error-warning-line"></i> Cannot connect to Orchestrator</div>`;
    }
}

// Render incident log
function renderIncidents(incidents) {
    incidentCount.textContent = `${incidents.length} Total`;
    
    // Update KPI Card
    const kpiIncidents = document.getElementById('kpi-incidents');
    if (kpiIncidents) kpiIncidents.textContent = incidents.length;
    
    incidentList.innerHTML = '';
    
    if (incidents.length === 0) {
        incidentList.innerHTML = `<div class="text-center text-slate-500 mt-10 text-sm italic">No incidents recorded.</div>`;
        return;
    }
    
    incidents.forEach(inc => {
        const date = new Date(inc.timestamp);
        
        // Ensure image_url is formatted as a local file URL if it's an absolute path
        const imageSrc = inc.image_url.startsWith('C:') ? `file:///${inc.image_url.replace(/\\/g, '/')}` : inc.image_url;
        
        const card = document.createElement('div');
        card.className = "bg-slate-800/80 border-l-4 border-red-500 rounded-lg p-3 text-sm shadow-md animate-fade-in transition hover:bg-slate-700/80 flex flex-col gap-2";
        card.innerHTML = `
            <!-- Header Row -->
            <div class="flex justify-between items-start">
                <div class="flex items-center gap-2">
                    <span class="bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase">Critical</span>
                    <span class="text-xs font-semibold text-white">Theft Detected</span>
                </div>
                <span class="text-[10px] text-slate-400 font-mono">${date.toLocaleTimeString()}</span>
            </div>
            
            <!-- Content Row with Thumbnail -->
            <div class="flex gap-3 mt-1 items-center">
                <!-- Thumbnail -->
                <div class="h-12 w-12 rounded bg-black border border-slate-700 overflow-hidden shrink-0 flex items-center justify-center">
                    ${inc.image_url ? `<img src="${imageSrc}" class="h-full w-full object-cover opacity-80 hover:opacity-100 transition">` : `<i class="ri-image-line text-slate-600"></i>`}
                </div>
                
                <!-- Details -->
                <div class="flex-1 flex flex-col gap-1">
                    <div class="text-slate-300 flex justify-between items-center text-xs">
                        <span class="flex items-center gap-1"><i class="ri-camera-lens-fill text-slate-500"></i> ${inc.camera_id}</span>
                        <span class="text-orange-300 font-mono">
                            ${(inc.confidence_score * 100).toFixed(1)}% Conf
                        </span>
                    </div>
                    
                    <!-- Action Button -->
                    <button class="text-xs bg-slate-700 hover:bg-slate-600 text-white rounded px-2 py-1 transition flex items-center justify-center gap-1 self-start mt-1" onclick="window.open('${imageSrc}', '_blank')">
                        <i class="ri-eye-line"></i> Review Full Frame
                    </button>
                </div>
            </div>
        `;
        incidentList.appendChild(card);
    });
}

// Handle simulate upload click
btnSimulate.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', async (e) => {
    if (!e.target.files.length) return;
    const file = e.target.files[0];
    
    // Stop webcam if running
    stopWebcam();
    
    // Show preview temporarily while processing
    const url = URL.createObjectURL(file);
    showPreview(url);
    
    // Process Frame
    await processFrame(file);
});

// Process a frame (either from webcam or upload)
async function processFrame(imageFile) {
    overlay.classList.remove('hidden');
    
    const formData = new FormData();
    formData.append('frame', imageFile);
    formData.append('camera_id', 'CAM-01');
    
    try {
        const response = await fetch(`${API_BASE}/process_frame/`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        overlay.classList.add('hidden');
        
        if (response.ok) {
            // Update the display with the annotated image from the ML service
            // Note: in a real production app, the backend would serve this image via a URL,
            // but for this prototype, we'll just leave the previous frame visible if clean
            
            if (result.status === 'incident_recorded') {
                triggerRedAlert();
                fetchIncidents(); // Refresh the list
            }
        } else {
            console.error('Server error:', result.error);
        }
        
    } catch (err) {
        console.error('Network error during frame processing:', err);
        overlay.classList.add('hidden');
    }
}

// UI Helpers
function showPreview(url) {
    placeholder.classList.add('hidden');
    webcamVideo.classList.add('hidden');
    resultImage.src = url;
    resultImage.classList.remove('hidden');
}

function triggerRedAlert() {
    mainContainer.classList.add('flash-red');
    setTimeout(() => {
        mainContainer.classList.remove('flash-red');
    }, 3000); // Stop flashing after 3 seconds
}

// Webcam Logic (Optional / Advanced)
async function startWebcam() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        webcamVideo.srcObject = stream;
        
        placeholder.classList.add('hidden');
        resultImage.classList.add('hidden');
        webcamVideo.classList.remove('hidden');
        
        btnWebcam.innerHTML = '<i class="ri-stop-circle-line"></i> Stop Webcam';
        btnWebcam.classList.replace('bg-slate-700', 'bg-red-600');
        btnWebcam.classList.replace('hover:bg-slate-600', 'hover:bg-red-500');
        
        // Setup capture interval (e.g. 1 frame every 3 seconds)
        // We capture video frame to canvas, then to blob, then to processFrame
        // (Omitted for prototype brevity unless specifically tested)
        
    } catch (err) {
        alert('Could not access webcam: ' + err.message);
    }
}

function stopWebcam() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
        
        webcamVideo.classList.add('hidden');
        placeholder.classList.remove('hidden');
        
        btnWebcam.innerHTML = '<i class="ri-vidicon-line"></i> Start Webcam';
        btnWebcam.classList.replace('bg-red-600', 'bg-slate-700');
        btnWebcam.classList.replace('hover:bg-red-500', 'hover:bg-slate-600');
    }
}

btnWebcam.addEventListener('click', () => {
    if (stream) stopWebcam();
    else startWebcam();
});
