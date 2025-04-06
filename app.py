from flask import Flask, render_template, jsonify, request
from proxmoxer import ProxmoxAPI
from db import init_db, insert_metric, get_metrics_history
from datetime import datetime, timedelta

app = Flask(__name__)

# Proxmox Connection
PROXMOX_HOST = ""
API_USER = ""
API_TOKEN = ""
VERIFY_SSL = False              # Using Self-Signed Cert.

def format_uptime(seconds):
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    return f"{days}d {hours}h {minutes}m"

@app.route('/')
def index():
    proxmox = ProxmoxAPI(
        PROXMOX_HOST,
        user=API_USER,
        token_name="tst-dashboard",
        token_value=API_TOKEN,
        verify_ssl=VERIFY_SSL
    )

    node_data = proxmox.nodes.get()
    info = []
    cluster_total_cpu = 0
    cluster_total_mem_used = 0
    cluster_total_mem_total = 0
    cluster_guest_count = 0

    for node in node_data:
        name = node['node']
        status = proxmox.nodes(name).status.get()
        print(f"DEBUG - Status for {name}: {status}")

        vms = proxmox.nodes(name).qemu.get()
        containers = proxmox.nodes(name).lxc.get()
        print(f"{name}: Found {len(vms)} VMs and {len(containers)} containers")

        all_guests = []

        cluster_total_cpu += status['cpu']
        cluster_total_mem_used += status['memory']['used']
        cluster_total_mem_total += status['memory']['total']

        # VMs
        for vm in vms:
            vm_id = vm['vmid']
            vm_status = proxmox.nodes(name).qemu(vm_id).status.current.get()

            all_guests.append({
                "id": vm_id,
                "name": vm.get('name', 'unknown'),
                "type": "VM",
                "status": vm_status['status'],
                "cpu": round(vm_status['cpu'] * 100, 2),
                "mem": round((vm_status['mem'] / vm_status['maxmem']) * 100, 2) if vm_status['maxmem'] > 0 else 0,
            })

        # LXCs
        for ct in containers:
            ct_id = ct['vmid']
            ct_status = proxmox.nodes(name).lxc(ct_id).status.current.get()

            all_guests.append({
                "id": ct_id,
                "name": ct.get('name', 'unknown'),
                "type": "LXC",
                "status": ct_status['status'],
                "cpu": round(ct_status['cpu'] * 100, 2),
                "mem": round((ct_status['mem'] / ct_status['maxmem']) * 100, 2) if ct_status['maxmem'] > 0 else 0,
            })

        cluster_guest_count += len(all_guests)

        info.append({
            "name": name,
            "cpu": round(status['cpu'] * 100, 2),
            "mem": round((status['memory']['used'] / status['memory']['total']) * 100, 2),
            "uptime": format_uptime(status['uptime']),
            "guests": all_guests
        })

    cluster_summary = {
        "nodes": len(info),
        "guests": cluster_guest_count,
        "cpu": round(cluster_total_cpu * 100 / len(info), 2),
        "mem": round((cluster_total_mem_used / cluster_total_mem_total) * 100, 2) if cluster_total_mem_total > 0 else 0
    }

    return render_template("index.html", nodes=info, summary=cluster_summary)

@app.route('/api/summary')
def summary_api():
    proxmox = ProxmoxAPI(
        PROXMOX_HOST,
        user=API_USER,
        token_name="tst-dashboard",
        token_value=API_TOKEN,
        verify_ssl=VERIFY_SSL
    )

    node_data = proxmox.nodes.get()

    cpu_total = 0
    mem_used = 0
    mem_total = 0

    for node in node_data:
        status = proxmox.nodes(node['node']).status.get()
        cpu_total += status['cpu']
        mem_used += status['memory']['used']
        mem_total += status['memory']['total']

    return jsonify({
        "cpu": round(cpu_total * 100 / len(node_data), 2),
        "mem": round((mem_used / mem_total) * 100, 2) if mem_total > 0 else 0
    })

@app.route('/api/nodes')
def node_metrics_api():
    proxmox = ProxmoxAPI(
        PROXMOX_HOST,
        user=API_USER,
        token_name="tst-dashboard",
        token_value=API_TOKEN,
        verify_ssl=VERIFY_SSL
    )

    nodes = proxmox.nodes.get()
    result = {}

    for node in nodes:
        name = node['node']
        status = proxmox.nodes(name).status.get()
        cpu = round(status['cpu'] * 100, 2)
        mem = round((status['memory']['used'] / status['memory']['total']) * 100, 2) if status['memory']['total'] > 0 else 0

        result[name] = { "cpu": cpu, "mem": mem }

        # ✅ Log into SQLite
        insert_metric(name, cpu, mem)

    return jsonify(result)

@app.route('/api/history/<node>')
def node_history(node):
    range_param = request.args.get("range", "100")

    if range_param.endswith("m"):
        # Time-based range, e.g., 60m = last 60 minutes
        minutes = int(range_param.rstrip("m"))
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        history = get_metrics_history(node, since=cutoff_time)
    else:
        # Default to latest N records
        try:
            limit = int(range_param)
        except ValueError:
            limit = 100
        history = get_metrics_history(node, limit=limit)

    return jsonify([
        {'timestamp': row[0], 'cpu': row[1], 'mem': row[2]} for row in history
    ])

# ✅ Init the DB when the app starts
init_db()

if __name__ == '__main__':
    app.run(debug=True)
