import subprocess
import socket
import sys

def check_connectivity(host, port):
    try:
        with socket.create_connection((host, port), timeout=5):
            return True
    except (socket.timeout, socket.error):
        return False

def check_ssh_connectivity(host):
    try:
        result = subprocess.run(['ssh', '-T', host], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        if result.returncode == 1:
            return True
    except subprocess.TimeoutExpired:
        pass
    return False
    
def check_ssh_connectivity_with_nc(host):
    try:
        result = subprocess.run(['nc', '-zv', host, '22'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        print(result.stdout.decode())  # Capturar i mostrar la sortida estàndard
        print(result.stderr.decode())  # Capturar i mostrar l'error estàndard
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"Timeout mentre es comprovava la connectivitat SSH amb {host}")
        return False
    except Exception as e:
        print(f"Error mentre es comprovava la connectivitat SSH amb {host}: {e}")
        return False

def clone_repository(repo_url):
    try:
        subprocess.run(['git', 'clone', repo_url], check=True)
    except subprocess.CalledProcessError:
        print(f"Error clonant el repositori {repo_url}")
        sys.exit(1)

# Comprovacions de connectivitat
if not check_ssh_connectivity('git@github.com'):
    print("No hi ha connectivitat amb github.com per SSH")
    sys.exit(1)

if not check_ssh_connectivity_with_nc('git@gitlab.ntt.ms'):
    print("No hi ha connectivitat amb gitlab.ntt.ms per SSH")
    sys.exit(1)

# Clonar el repositori si hi ha connectivitat
clone_repository('git@github.com:marcmoiagese/pybunpwsh.git')

# Comprovacions de connectivitat a altres adreces IP i ports
checks = [
    ('evl6800756.sys.ntt.eu', 443),
    ('eve6800500.sys.ntt.eu', 443),
    ('eve2400500.sys.ntt.eu', 443),
    ('192.168.190.232', 22),
    ('192.168.58.237', 22)
]

for host, port in checks:
    if not check_connectivity(host, port):
        print(f"No hi ha connectivitat amb {host} al port {port}")
        sys.exit(1)

print("Totes les comprovacions han passat correctament.")
