import subprocess
import socket
import sys
import os
import shutil

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
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False

def clone_repository(repo_url):
    try:
        subprocess.run(['git', 'clone', repo_url], check=True)
        return True
    except subprocess.CalledProcessError:
        print(f"Error clonant el repositori {repo_url}")
        return False

def copy_ssh_keys(target_dir):
    ssh_dir = os.path.expanduser("~/.ssh")
    id_rsa = os.path.join(ssh_dir, "id_rsa")
    id_rsa_pub = os.path.join(ssh_dir, "id_rsa.pub")
    
    if not os.path.exists(id_rsa) or not os.path.exists(id_rsa_pub):
        print("  ____  _                                     _                  _            _ _   _   _  __ _            ")
        print(" |  _ \\| | __ _ _   _  __ _  __ _  ___       | |_ _ __ _   _  ___| |_ ___ _ __(_) |_| |_| |/ _(_)_ __   ___ ")
        print(" | |_) | |/ _` | | | |/ _` |/ _` |/ _ \\  _   | __| '__| | | |/ __| __/ _ \\ '__| | __| __| | |_| | '_ \\ / _ \\")
        print(" |  __/| | (_| | |_| | (_| | (_| |  __/ | |__| |_| |  | |_| | (__| ||  __/ |  | | |_| |_| |  _| | | | |  __/")
        print(" |_|   |_|\\__,_|\\__, |\\__,_|\\__, |\\___|  \\____/\\__|_|   \\__,_|\\___|\\__\\___|_|  |_|\\__|\\__|_| |_|_| |_|\\___|")
        print("                |___/       |___/                                                                          ")
        print("Please generate a new SSH key and add it to GitLab.")
        sys.exit(1)
    
    try:
        os.makedirs(target_dir, exist_ok=True)
        shutil.copy(id_rsa, target_dir)
        shutil.copy(id_rsa_pub, target_dir)
        print(f"Les claus SSH s'han copiat correctament a {target_dir}")
    except Exception as e:
        print(f"Error copiant les claus SSH: {e}")
        sys.exit(1)

def create_docker_compose_file(target_dir):
    docker_compose_content = """version: '3.8'

name: Scripts
services:
  scripts:
    build: .
    volumes:
      - scripts:/home/nttrmadm/reports
    environment:
      MYHOSTNAME: "evl2401011"
      MYDOMAIN: "sys.ntt.eu"
      MYORIGIN: "sys.ntt.eu"
      MYDESTINATION: "evl2401011, evl2403003, localhost.localdomain, localhost, evl2401011.sys.ntt.eu, sys.ntt.eu"
      RELAYHOST: "13.95.145.251"
    extra_hosts:
      - "eve6800500.sys.ntt.eu:192.168.190.253"
      
volumes:
  scripts:
"""
    try:
        file_path = os.path.join(target_dir, 'docker-compose.yml')
        with open(file_path, 'w') as file:
            file.write(docker_compose_content)
        print(f"El fitxer docker-compose.yml s'ha creat correctament a {target_dir}")
    except Exception as e:
        print(f"Error creant el fitxer docker-compose.yml: {e}")
        sys.exit(1)

def create_docker_compose_override_file(target_dir, citrix_password, lb_pass_pp, lb_pass_prod):
    docker_compose_override_content = f"""version: '3.8'

services:
  scripts:
    environment:
      CITRIX_PASSWORD: "{citrix_password}"
      LB_PASS_PROD: "{lb_pass_prod}"
      LB_PASS_PP: "{lb_pass_pp}"
"""
    try:
        file_path = os.path.join(target_dir, 'docker-compose.override.yml')
        with open(file_path, 'w') as file:
            file.write(docker_compose_override_content)
        print(f"El fitxer docker-compose.override.yml s'ha creat correctament a {target_dir}")
    except Exception as e:
        print(f"Error creant el fitxer docker-compose.override.yml: {e}")
        sys.exit(1)

def run_docker_compose_up(target_dir):
    try:
        subprocess.run(['docker', 'compose', 'up', '-d'], cwd=target_dir, check=True)
        print("Els serveis de Docker s'han iniciat correctament.")
    except subprocess.CalledProcessError as e:
        print(f"Error executant 'docker compose up -d': {e}")
        sys.exit(1)

# Eliminar el directori ./pybunpwsh si ja existeix
if os.path.exists('./pybunpwsh'):
    try:
        shutil.rmtree('./pybunpwsh')
        print("El directori ./pybunpwsh s'ha eliminat correctament.")
    except Exception as e:
        print(f"Error eliminant el directori ./pybunpwsh: {e}")
        sys.exit(1)

# Comprovacions de connectivitat
if not check_ssh_connectivity('git@github.com'):
    print("No hi ha connectivitat amb github.com per SSH")
    sys.exit(1)

if not check_ssh_connectivity_with_nc('gitlab.ntt.ms'):
    print("No hi ha connectivitat amb gitlab.ntt.ms per SSH")
    sys.exit(1)

# Clonar el repositori si hi ha connectivitat
if not clone_repository('git@github.com:marcmoiagese/pybunpwsh.git'):
    sys.exit(1)

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
        
# Copiar les claus SSH al directori del repositori clonat
copy_ssh_keys('./pybunpwsh')

# Crear el fitxer docker-compose.yml
create_docker_compose_file('./pybunpwsh')

# Demanar contrasenyes a l'usuari
citrix_password = input("Introdueix la contrasenya per l'ID PWD000050496: ")
lb_pass_pp = input("Introdueix la contrasenya per l'ID PWD000045386: ")
lb_pass_prod = input("Introdueix la contrasenya per l'ID PWD000050492: ")

# Crear el fitxer docker-compose.override.yml amb les contrasenyes introduïdes
create_docker_compose_override_file('./pybunpwsh', citrix_password, lb_pass_pp, lb_pass_prod)

# Executar 'docker compose up -d' per iniciar els serveis
run_docker_compose_up('./pybunpwsh')

print("Totes les comprovacions han passat correctament.")
