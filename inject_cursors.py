import os
import re

INDEX_PATH = "/Users/Apple/Desktop/tunnel/frontend/index.html"

with open(INDEX_PATH, "r") as f:
    html = f.read()

# Add CSS for cursors before </style>
cursor_css = """
/* Live Cursors */
.live-cursor {
    position: absolute;
    pointer-events: none;
    z-index: 9999;
    transition: transform 0.05s linear;
}
.live-cursor svg {
    width: 20px;
    height: 20px;
    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));
}
.live-cursor-name {
    position: absolute;
    top: 20px;
    left: 12px;
    background: var(--color);
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 700;
    white-space: nowrap;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4);
}
"""

if "/* Live Cursors */" not in html:
    html = html.replace("</style>", cursor_css + "\n</style>")

# Add JS for cursors before closing </script>
cursor_js = """
// --- LIVE CURSORS ---
const cursors = {};
const colors = ['#6366f1', '#ec4899', '#f59e0b', '#10b981', '#8b5cf6', '#ef4444'];

function getCursorColor(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
}

let lastCursorEmit = 0;
document.addEventListener('mousemove', e => {
    const now = Date.now();
    if (now - lastCursorEmit > 50 && wsCode) {
        lastCursorEmit = now;
        const xPct = e.clientX / window.innerWidth;
        const yPct = e.clientY / window.innerHeight;
        socket.emit('cursor_move', { code: wsCode, x: xPct, y: yPct });
    }
});

socket.on('cursor_moved', data => {
    const { sid, name, x, y } = data;
    if (sid === socket.id) return;
    
    let cursor = document.getElementById('cursor-' + sid);
    if (!cursor) {
        const color = getCursorColor(name);
        cursor = document.createElement('div');
        cursor.id = 'cursor-' + sid;
        cursor.className = 'live-cursor';
        cursor.style.setProperty('--color', color);
        cursor.innerHTML = `
            <svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M1.20015 1.15783L5.80808 14.516C6.18321 15.6039 7.69614 15.656 8.14811 14.596L10.3704 9.38289C10.4578 9.17789 10.6176 9.01423 10.8202 8.92211L15.9314 6.59809C16.9712 6.12543 16.8929 4.60627 15.7925 4.22591L2.46313 0.655815C1.41165 0.374246 0.455246 1.45524 0.771946 2.47867L1.20015 1.15783Z" fill="${color}"/>
                <path d="M1.20015 1.15783L5.80808 14.516C6.18321 15.6039 7.69614 15.656 8.14811 14.596L10.3704 9.38289C10.4578 9.17789 10.6176 9.01423 10.8202 8.92211L15.9314 6.59809C16.9712 6.12543 16.8929 4.60627 15.7925 4.22591L2.46313 0.655815C1.41165 0.374246 0.455246 1.45524 0.771946 2.47867L1.20015 1.15783Z" stroke="white" stroke-width="1.5" stroke-linejoin="round"/>
            </svg>
            <div class="live-cursor-name">${name}</div>
        `;
        document.body.appendChild(cursor);
        cursors[sid] = cursor;
    }
    
    const absX = x * window.innerWidth;
    const absY = y * window.innerHeight;
    cursor.style.transform = `translate(${absX}px, ${absY}px)`;
    
    // Auto-hide after 10 seconds of no movement
    clearTimeout(cursor.hideTimeout);
    cursor.style.opacity = 1;
    cursor.hideTimeout = setTimeout(() => {
        cursor.style.opacity = 0;
    }, 10000);
});

socket.on('workspace_joined', d => {
    // Keep existing workspace_joined logic but clean up stale cursors
    // The existing code handles rendering members, we just need to delete missing cursors
    Object.keys(cursors).forEach(sid => {
        if (!members[sid]) {
            if (cursors[sid].parentNode) cursors[sid].parentNode.removeChild(cursors[sid]);
            delete cursors[sid];
        }
    });
});

// Also remove cursor when someone leaves
const origPeerLeft = socket._callbacks['$peer_left'];
socket.on('peer_left', d => {
    if (cursors[d.sid]) {
        if (cursors[d.sid].parentNode) cursors[d.sid].parentNode.removeChild(cursors[d.sid]);
        delete cursors[d.sid];
    }
});
"""

if "// --- LIVE CURSORS ---" not in html:
    html = html.replace("</script>\n</body>", cursor_js + "\n</script>\n</body>")
    
with open(INDEX_PATH, "w") as f:
    f.write(html)
    
print("Cursors injected!")
