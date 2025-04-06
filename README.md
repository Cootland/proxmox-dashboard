# Proxmox Cluster Dashboard

## 🛠 Requirements

- Python 3.10+
- Proxmox API Token with audit permissions
- Flask
- Chart.js (via CDN)
- SQLite3 (bundled with Python)

## 📦 Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/cootland/proxmox-dashboard.git
   cd proxmox-dashboard
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Set your Proxmox API config in `app.py`:
   ```python
   PROXMOX_HOST = "10.190.0.10"
   API_USER = "api@pve"
   API_TOKEN = "your-token"
   VERIFY_SSL = False  # if using self-signed cert
   ```

4. Run the app:
   ```bash
   python app.py
   ```

5. Open your browser:
   ```
   http://localhost:5000
   ```

## 🧠 Architecture

- `app.py`: Flask backend + Proxmox API integration
- `db.py`: SQLite metric logging
- `templates/index.html`: Dashboard UI with dynamic graphs
- `/api/nodes`, `/api/summary`, `/api/history/<node>`: JSON endpoints

## 📜 License

MIT License — free to use, modify, and deploy.
