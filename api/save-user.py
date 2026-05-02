import json
import os
from http.server import BaseHTTPRequestHandler
from datetime import datetime

try:
    import redis
    # Connect to Vercel KV
    kv_url = os.environ.get("KV_URL")
    if kv_url:
        r = redis.from_url(kv_url)
    else:
        r = None
except ImportError:
    r = None

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        # Allow CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            name = data.get('name')
            age = data.get('age')
            gender = data.get('gender')
            
            if not name or not age or not gender:
                self.wfile.write(json.dumps({'success': False, 'message': 'Missing required fields'}).encode('utf-8'))
                return
                
            new_user = {
                'id': str(datetime.now().timestamp()),
                'name': name,
                'age': age,
                'gender': gender,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save to Vercel KV Database if configured
            if r:
                r.lpush("users_data", json.dumps(new_user))
                self.wfile.write(json.dumps({'success': True, 'message': 'User saved permanently to Vercel KV!', 'user': new_user}).encode('utf-8'))
            else:
                # Fallback to local temporary save (only works on local dev, not Vercel production)
                try:
                    root_dir = os.path.join(os.path.dirname(__file__), '..')
                    file_path = os.path.join(root_dir, 'users.json')
                    
                    users = []
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            users = json.load(f)
                    users.append(new_user)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(users, f, indent=2)
                    self.wfile.write(json.dumps({'success': True, 'message': 'Saved locally (Redis not configured)', 'user': new_user}).encode('utf-8'))
                except Exception as e:
                    self.wfile.write(json.dumps({'success': False, 'message': f'Redis not configured and local save failed: {e}'}).encode('utf-8'))

        except Exception as e:
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode('utf-8'))

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
