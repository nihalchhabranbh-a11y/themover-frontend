import os
import re

INDEX_PATH = "/Users/Apple/Desktop/tunnel/frontend/index.html"

with open(INDEX_PATH, "r") as f:
    original_html = f.read()

# Extract script
script_match = re.search(r'<script>(.*?)</script>', original_html, re.DOTALL)
if not script_match:
    print("Could not find script block")
    exit(1)
script_content = script_match.group(1)

# Modify script content to add new features
script_content = script_content.replace(
    "socket.on('call_peer_joined', d => {",
    """
    // NEW EVENTS
    socket.on('file_uploaded', d => { loadFiles(); });
    socket.on('file_deleted', d => { loadFiles(); });
    socket.on('workspace_renamed', d => { 
        wsName = d.new_name; 
        localStorage.setItem('ws_name', wsName);
        document.getElementById('ws-name-display').textContent = wsName;
    });
    socket.on('you_are_kicked', () => {
        alert("You have been removed from the workspace by the admin.");
        window.location.href = '/workspace.html';
    });

    socket.on('call_peer_joined', d => {"""
)

# Admin functions
admin_js = """
// Admin controls
function deleteFile(publicId) {
    if(confirm('Are you sure you want to delete this file for everyone?')) {
        socket.emit('delete_file', { code: wsCode, name: userName, public_id: publicId });
    }
}
function kickUser(sid) {
    if(confirm('Kick this user out of the workspace?')) {
        socket.emit('kick_user', { code: wsCode, name: userName, target_sid: sid });
    }
}
function renameWorkspace() {
    const newName = prompt('Enter new workspace name:');
    if (newName) socket.emit('rename_workspace', { code: wsCode, name: userName, new_name: newName });
}

// PiP drag logic
const pip = document.getElementById('pip-video');
let isDragging = false, startX, startY, initX, initY;
pip.addEventListener('mousedown', e => {
    isDragging = true; startX = e.clientX; startY = e.clientY;
    const rect = pip.getBoundingClientRect();
    initX = rect.left; initY = rect.top;
});
document.addEventListener('mousemove', e => {
    if(!isDragging) return;
    pip.style.left = initX + e.clientX - startX + 'px';
    pip.style.top = initY + e.clientY - startY + 'px';
    pip.style.bottom = 'auto'; pip.style.right = 'auto';
});
document.addEventListener('mouseup', () => isDragging = false);

function closePip() {
    pip.style.display = 'none';
    document.getElementById('meet-call').appendChild(document.getElementById('video-grid'));
}

const origSwitchTab = switchTab;
window.switchTab = function(t) {
    if (inCall && t !== 'meet') {
        const grid = document.getElementById('video-grid');
        document.getElementById('pip-container').appendChild(grid);
        pip.style.display = 'block';
    } else if (t === 'meet') {
        pip.style.display = 'none';
        document.getElementById('meet-call').insertBefore(document.getElementById('video-grid'), document.getElementById('call-controls'));
    }
    origSwitchTab(t);
};
"""

script_content += "\n" + admin_js

# Override loadFiles to inject admin delete button logic
script_content = script_content.replace(
    "card.innerHTML = `",
    """
    let deleteBtn = '';
    // If admin is active, show delete btn. (A real app would securely verify admin status on backend, but we'll show UI based on simple rules)
    deleteBtn = `<button class="fc-btn" onclick="deleteFile('${f.public_id}')" style="color:#ef4444; border-color:#ef4444; margin-right:8px;">Delete</button>`;
    
    card.innerHTML = `"""
)

# Also update member rendering to include kick button
script_content = script_content.replace(
    "document.getElementById('panel-members').innerHTML =",
    "// render members logic is below"
)


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>TheMover Workspace</title>
<link rel="manifest" href="/manifest.json"/>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🚀</text></svg>">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Material+Symbols+Outlined:wght,FILL@400,0..1&display=swap" rel="stylesheet"/>
<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrious/4.0.2/qrious.min.js"></script>
<script src="https://unpkg.com/html5-qrcode"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/lz-string/1.5.0/lz-string.min.js"></script>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #0d0d17;
  --sidebar: #111118;
  --card: #1a1a2e;
  --border: #2a2a4a;
  --primary: #6366f1;
  --primary-hover: #4f46e5;
  --text: #f0f0f8;
  --muted: #9ca3af;
  --danger: #ef4444;
  --success: #22c55e;
}
body { font-family: 'Inter', sans-serif; background-color: var(--bg); color: var(--text); display: flex; height: 100vh; overflow: hidden; }

/* Sidebar */
#sidebar { width: 260px; min-width: 260px; background-color: var(--sidebar); border-right: 1px solid var(--border); display: flex; flex-direction: column; padding: 24px 16px; z-index: 10; }
.brand { font-size: 20px; font-weight: 800; display: flex; align-items: center; gap: 10px; margin-bottom: 24px; }
.brand .badge { font-size: 10px; background: rgba(99, 102, 241, 0.2); color: var(--primary); padding: 2px 6px; border-radius: 6px; }
.ws-pill { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 12px; display: flex; align-items: center; gap: 12px; margin-bottom: 24px; cursor: pointer; }
.ws-avatar { width: 32px; height: 32px; border-radius: 8px; background: linear-gradient(135deg, #f59e0b, #ef4444); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; }
.ws-info { flex: 1; min-width: 0; }
.ws-name { font-size: 14px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ws-status { font-size: 11px; color: var(--muted); display: flex; align-items: center; gap: 4px; margin-top: 2px; }
.ws-status .dot { width: 6px; height: 6px; background: var(--success); border-radius: 50%; }

.nav-btn { display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-radius: 8px; color: var(--muted); font-size: 14px; font-weight: 500; cursor: pointer; border: none; background: transparent; width: 100%; text-align: left; transition: all 0.2s; position: relative; margin-bottom:4px; }
.nav-btn:hover { background: rgba(255,255,255,0.03); color: var(--text); }
.nav-btn.active { background: #1e1e2e; color: var(--text); }
.nav-btn.active::before { content: ''; position: absolute; left: 0; top: 8px; bottom: 8px; width: 3px; background: var(--primary); border-radius: 0 4px 4px 0; }
.nav-btn .icon { font-size: 18px; font-family: 'Material Symbols Outlined'; }

.sidebar-footer { margin-top: auto; display: flex; flex-direction: column; gap: 6px; }
.flash-btn { background: var(--primary); color: white; border: none; border-radius: 12px; padding: 12px; font-size: 14px; font-weight: 600; cursor: pointer; margin-bottom: 16px; transition: background 0.2s; width:100%; }
.flash-btn:hover { background: var(--primary-hover); }

.user-row { display: flex; align-items: center; gap: 12px; padding: 8px; }
.user-avatar { width: 28px; height: 28px; border-radius: 50%; background: #374151; display: flex; align-items: center; justify-content: center; font-size: 12px; }
.user-name { font-size: 13px; font-weight: 500; }

/* Main */
#main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.header { height: 72px; padding: 0 32px; border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; }
.breadcrumb { font-size: 14px; color: var(--muted); }
.breadcrumb span { color: var(--text); font-weight: 500; }
.header-actions { display: flex; gap: 12px; }
.btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer; }
.btn-outline:hover { background: rgba(255,255,255,0.05); }

.panel { flex: 1; display: none; flex-direction: column; overflow-y: auto; padding: 32px; }
.panel.active { display: flex; }

/* Files */
#drop-zone { background: #16162a; border: 1.5px dashed rgba(99, 102, 241, 0.3); border-radius: 16px; padding: 40px; text-align: center; margin-bottom: 24px; transition: all 0.2s; position: relative; }
#drop-zone.drag { border-color: var(--primary); background: rgba(99, 102, 241, 0.05); }
#drop-zone input[type="file"] { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
.dz-icon { font-size: 48px; color: var(--primary); margin-bottom: 16px; display: block; font-family: 'Material Symbols Outlined'; }
.dz-title { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
.dz-sub { color: var(--muted); font-size: 14px; margin-bottom: 16px; }

.progress-bar-wrap { margin-bottom: 24px; display: none; }
.up-bar-bg { height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
.progress-bar { height: 100%; background: var(--primary); width: 0%; transition: width 0.3s; }
.up-text { font-size: 12px; color: var(--muted); margin-top: 8px; display: flex; justify-content: space-between; }

#file-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; align-items:start;}
.file-card { background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 16px; display: flex; align-items: center; gap: 16px; }
.file-icon { width: 48px; height: 48px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 24px; font-family: 'Material Symbols Outlined'; background: rgba(255,255,255,0.05); }
.file-info { flex: 1; min-width: 0; }
.file-name { font-size: 14px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px; }
.file-size { font-size: 12px; color: var(--muted); display: flex; align-items: center; gap: 8px; }
.dl-btn { background: transparent; border: 1px solid var(--border); color: var(--text); padding: 6px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; }
.dl-btn:hover { background: rgba(255,255,255,0.05); }

/* Chat */
#chat-messages { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; padding-bottom: 20px; }
.msg { display: flex; gap: 12px; max-width: 80%; flex-direction:column; }
.msg.mine { align-self: flex-end; }
.msg-name { font-size: 12px; color: var(--muted); }
.msg.mine .msg-name { text-align:right;}
.msg-bubble { background: var(--card); padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.5; border: 1px solid var(--border); }
.msg.mine .msg-bubble { background: var(--primary); border-color: var(--primary); color: white; }
.chat-input-wrap { margin-top: auto; display: flex; gap: 12px; }
.chat-input { flex: 1; background: var(--card); border: 1px solid var(--border); padding: 14px 16px; border-radius: 12px; color: var(--text); font-size: 14px; outline: none; }
.chat-input:focus { border-color: var(--primary); }
.send-btn { background: var(--primary); color: white; border: none; width: 48px; border-radius: 12px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 18px; font-family:'Material Symbols Outlined'; }

/* Meet */
#meet-lobby { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; }
.join-call-btn { background: var(--primary); color: #fff; border: none; border-radius: 14px; padding: 14px 32px; font-size: 16px; font-weight: 700; cursor: pointer; }
#meet-call { flex: 1; display: none; flex-direction: column; }
#video-grid { flex: 1; display: grid; gap: 8px; padding: 16px; background: #000; overflow: hidden; }
.video-tile { position: relative; background: #111; border-radius: 12px; overflow: hidden; }
.video-tile video { width: 100%; height: 100%; object-fit: cover; }
.tile-name { position: absolute; bottom: 8px; left: 8px; font-size: 11px; font-weight: 700; background: rgba(0, 0, 0, .6); padding: 3px 8px; border-radius: 20px; }
#call-controls { padding: 12px; background: #0a0a1a; display: flex; justify-content: center; gap: 12px; }
.ctrl-btn { background: rgba(255, 255, 255, .1); border: none; border-radius: 50%; width: 48px; height: 48px; font-size: 20px; cursor: pointer; color: #fff; font-family: 'Material Symbols Outlined'; transition: background .15s; display:flex; align-items:center; justify-content:center;}
.ctrl-btn.danger { background: var(--danger); }

/* PiP */
.pip-video { position: fixed; bottom: 24px; right: 24px; width: 280px; height: 180px; background: #000; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); overflow: hidden; z-index: 100; display: none; border: 1px solid var(--border); cursor: grab; }
.pip-video:active { cursor: grabbing; }
.pip-badge { position: absolute; top: 12px; left: 12px; background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); padding: 4px 8px; border-radius: 20px; font-size: 11px; font-weight: 600; display: flex; align-items: center; gap: 4px; z-index:10; }
.pip-badge .dot { width: 6px; height: 6px; background: var(--success); border-radius: 50%; }
.pip-close { position: absolute; top: 12px; right: 12px; background: rgba(0,0,0,0.6); border: none; color: white; width: 24px; height: 24px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 14px; z-index:10; }
#pip-container {width:100%; height:100%; position:absolute; inset:0; pointer-events:none;}
#pip-container #video-grid { padding:0; gap:0;}
#pip-container .video-tile { border-radius:0; }

/* Members & Admin */
.admin-btn { background:var(--primary); color:white; border:none; padding:6px 12px; border-radius:6px; cursor:pointer; font-size:12px; margin-left:auto;}
.member-item { display:flex; align-items:center; gap:12px; padding:12px 0; border-bottom:1px solid var(--border);}
.member-avatar { width:32px; height:32px; background:var(--primary); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:14px; font-weight:bold;}

/* Modal */
.modal-bg { position: fixed; inset: 0; background: rgba(0,0,0,0.8); backdrop-filter: blur(4px); display: none; align-items: center; justify-content: center; z-index: 200; }
.modal-bg.open { display: flex; }
.modal-sheet { background: var(--card); border: 1px solid var(--border); border-radius: 20px; width: 100%; max-width: 400px; padding: 24px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.modal-close { background: none; border: none; color: var(--muted); font-size: 24px; cursor: pointer; }
.xender-input { width:100%; padding:12px; background:#111118; border:1px solid var(--border); color:white; border-radius:8px; margin-bottom:12px;}
.xender-btn { background:var(--primary); color:white; padding:10px 16px; border:none; border-radius:8px; width:100%; cursor:pointer; font-weight:600; margin-bottom:8px;}
.xender-btn.secondary { background:#111118; border:1px solid var(--border); }
</style>
</head>
<body>

<div id="sidebar">
    <div class="brand">🚀 TheMover <span class="badge">v2</span></div>
    
    <div class="ws-pill" onclick="renameWorkspace()">
        <div class="ws-avatar" id="ws-avatar-initial">W</div>
        <div class="ws-info">
            <div class="ws-name" id="ws-name-display">Workspace</div>
            <div class="ws-status"><div class="dot"></div> Online</div>
        </div>
    </div>
    
    <button class="nav-btn active" id="tab-files" onclick="switchTab('files')">
        <span class="icon">folder</span> Files
    </button>
    <button class="nav-btn" id="tab-chat" onclick="switchTab('chat')">
        <span class="icon">chat</span> Chat
    </button>
    <button class="nav-btn" id="tab-meet" onclick="switchTab('meet')">
        <span class="icon">videocam</span> Meet
    </button>
    <button class="nav-btn" id="tab-members" onclick="switchTab('members')">
        <span class="icon">group</span> Members
    </button>
    
    <div class="sidebar-footer">
        <button class="flash-btn" onclick="openFlash()">⚡ Flash Share</button>
        <div class="user-row">
            <div class="user-avatar" id="user-avatar-initial">U</div>
            <div class="user-name" id="user-name-display">User</div>
        </div>
    </div>
</div>

<div id="main">
    <div class="header">
        <div class="breadcrumb" id="header-breadcrumb">Workspace <span>/ Files</span></div>
        <div class="header-actions">
            <button class="btn-outline" onclick="copyInvite()">Invite</button>
        </div>
    </div>
    
    <!-- Files -->
    <div class="panel active" id="panel-files">
        <div id="drop-zone" onclick="document.getElementById('file-upload').click()">
            <input type="file" id="file-upload" multiple>
            <span class="icon dz-icon">cloud_upload</span>
            <div class="dz-title">Drag & drop files here</div>
            <div class="dz-sub">or click to browse • Supports any file up to 20GB</div>
            <button class="xender-btn" style="width:auto; border-radius:20px; padding:8px 24px;">Choose Files</button>
        </div>
        
        <div class="progress-bar-wrap" id="progress-wrap">
            <div class="up-bar-bg"><div class="progress-bar" id="progress-bar"></div></div>
            <div class="up-text">
                <span id="progress-filename">Uploading...</span>
                <span id="progress-pct">0%</span>
            </div>
        </div>
        
        <div id="file-list"></div>
    </div>
    
    <!-- Chat -->
    <div class="panel" id="panel-chat">
        <div id="chat-messages"></div>
        <div class="chat-input-wrap">
            <input type="text" class="chat-input" id="chat-input" placeholder="Type a message...">
            <button class="send-btn" onclick="sendChat()">send</button>
        </div>
    </div>
    
    <!-- Meet -->
    <div class="panel" id="panel-meet">
        <div id="meet-lobby">
            <div class="dz-icon" style="font-size:64px;">videocam</div>
            <div class="meet-title">Video Meeting</div>
            <div class="meet-sub">Join the call with your workspace members</div>
            <button class="join-call-btn" onclick="joinCall()">Join Call</button>
        </div>
        <div id="meet-call">
            <div id="video-grid"></div>
            <div id="call-controls">
                <button class="ctrl-btn" id="btn-mic" onclick="toggleMic()">mic</button>
                <button class="ctrl-btn" id="btn-cam" onclick="toggleCam()">videocam</button>
                <button class="ctrl-btn" id="btn-screen" onclick="toggleScreen()">present_to_all</button>
                <button class="ctrl-btn danger" onclick="leaveCall()">call_end</button>
            </div>
        </div>
    </div>
    
    <!-- Members & Admin -->
    <div class="panel" id="panel-members">
        <div class="dz-title">Workspace Members</div>
        <div class="dz-sub">Manage people currently online in this workspace.</div>
        <div id="members-list" style="margin-top:24px;"></div>
    </div>
</div>

<!-- PiP Video -->
<div class="pip-video" id="pip-video">
    <div class="pip-badge"><div class="dot"></div> Live</div>
    <button class="pip-close" onclick="closePip()">×</button>
    <div id="pip-container"></div>
</div>

<!-- Flash Share Modal (unchanged structure to keep JS happy) -->
<div class="modal-bg" id="flashModal">
    <div class="modal-sheet">
        <div class="modal-header">
            <h3>⚡ Flash Share</h3>
            <button class="modal-close" onclick="closeFlash()">×</button>
        </div>
        <div class="modal-body">
            <div style="display:flex; gap:8px; margin-bottom:16px;">
                <button class="xender-btn secondary" id="xtab-send" onclick="switchXTab('send')">Send</button>
                <button class="xender-btn secondary" id="xtab-receive" onclick="switchXTab('receive')">Receive</button>
            </div>
            <div id="xsend">
                <input type="file" id="xenderFileInput" style="display:none" onchange="xenderFileSelected(this)">
                <button class="xender-btn" id="xChooseBtn" onclick="document.getElementById('xenderFileInput').click()">Choose File to Send</button>
                <div id="xQrArea" style="display:none;text-align:center;">
                    <p id="xFileName" style="font-weight:700;margin-bottom:12px;"></p>
                    <p id="xSendStatus" style="font-size:12px;color:var(--muted);margin-bottom:8px;"></p>
                    <canvas id="qrcode" style="border-radius:12px;max-width:220px;width:100%;"></canvas>
                    <button class="xender-btn secondary" id="xCopyOffer" onclick="copyXCode('offer')" style="display:none">Copy Code</button>
                    <div id="xManualAnswer" style="display:none;margin-top:12px;">
                        <input class="xender-input" id="manualAnswerInput" placeholder="Paste Answer Code">
                        <button class="xender-btn" onclick="handleManualAnswer()">Connect</button>
                    </div>
                    <button class="xender-btn secondary" id="xScanAnswerBtn" onclick="startSenderScanner()">Scan Answer QR</button>
                    <div id="sender-qr-reader" style="display:none;max-width:250px;min-height:220px;margin:12px auto;border-radius:12px;overflow:hidden;"></div>
                </div>
            </div>
            <div id="xreceive" style="display:none;">
                <p style="font-size:13px;color:var(--muted);margin-bottom:12px;text-align:center;">Scan the sender's QR code to connect.</p>
                <button class="xender-btn" id="xScanOfferBtn" onclick="startReceiverScanner()">Open Camera</button>
                <div id="qr-reader" style="max-width:250px;min-height:220px;margin:0 auto;border-radius:12px;overflow:hidden;"></div>
                <div style="margin-top:16px;text-align:center;">
                    <p style="font-size:12px;color:var(--muted);margin-bottom:8px;">Or paste manual code</p>
                    <input class="xender-input" id="manualOfferInput" placeholder="Paste Offer Code">
                    <button class="xender-btn secondary" onclick="handleManualOffer()">Connect</button>
                </div>
            </div>
            <div id="xReceiveStep2" style="display:none;text-align:center;">
                <p id="xReceiveStatus" style="font-size:12px;color:var(--muted);margin-bottom:8px;"></p>
                <canvas id="qrcodeAnswer" style="border-radius:12px;max-width:220px;width:100%;"></canvas>
                <button class="xender-btn secondary" onclick="copyXCode('answer')">Copy Code</button>
            </div>
            <div id="xTransfer" style="display:none;text-align:center;">
                <div class="dz-icon" style="font-size:48px;">swap_vert</div>
                <p id="xTransferDetail" style="font-weight:700;margin-bottom:16px;"></p>
                <div class="up-bar-bg" style="margin-bottom:8px;"><div class="progress-bar" id="xProgressFill"></div></div>
                <p id="xProgressText" style="font-size:12px;color:var(--primary);">0%</p>
            </div>
        </div>
    </div>
</div>

<script>
"""

HTML += script_content + "\n</body>\n</html>"

# Override the renderMembers function inside script_content using regex
def override_render_members(match):
    return """
    const list = document.getElementById('members-list');
    list.innerHTML = '';
    const sidMap = {};
    Object.keys(members).forEach(sid => {
        const m = members[sid];
        const isMe = sid === socket.id;
        const av = m.name.charAt(0).toUpperCase();
        
        let kickHtml = '';
        if(!isMe) kickHtml = `<button class="admin-btn" style="background:#ef4444;" onclick="kickUser('${sid}')">Kick</button>`;
        
        list.innerHTML += `
        <div class="member-item">
            <div class="member-avatar">${av}</div>
            <div style="flex:1;">
                <div style="font-weight:600;font-size:14px;">${m.name} ${isMe ? '<span style="color:var(--muted);font-size:12px;">(You)</span>' : ''}</div>
            </div>
            ${kickHtml}
        </div>
        `;
    });
    """

HTML = re.sub(r'document\.getElementById\(\'panel-members\'\)\.innerHTML =.*?;(?=\s*\})', override_render_members, HTML, flags=re.DOTALL)


with open("index_new.html", "w") as f:
    f.write(HTML)

print("Generated index_new.html")
