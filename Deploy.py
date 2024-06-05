import subprocess
import socket
import sys
import os
import shutil
import tempfile

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

name: scripts
services:
  scripts:
    build: .
    volumes:
      - scripts:/home/usuari/reports
    environment:
      MYHOSTNAME: "test"
      MYDOMAIN: "mdemarc.com"
      MYORIGIN: "mdemarc.com"
      MYDESTINATION: "localhost.localdomain, localhost, mdemarc.com"
      RELAYHOST: "53.92.20.15"
      
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

def get_container_id(service_name):
    try:
        result = subprocess.run(['docker', 'ps', '-q', '--format', '{{.ID}}', '--latest'], stdout=subprocess.PIPE, check=True)
        container_id = result.stdout.decode().strip()
        if not container_id:
            print("No s'ha trobat cap contenidor en execució.")
            sys.exit(1)
        return container_id
    except subprocess.CalledProcessError as e:
        print(f"Error obtenint l'ID del contenidor: {e}")
        sys.exit(1)

def get_latest_container_id():
    try:
        result = subprocess.run(['docker', 'ps', '-q', '--format', '{{.ID}}', '--latest'], stdout=subprocess.PIPE, check=True)
        container_id = result.stdout.decode().strip()
        if not container_id:
            print("No s'ha trobat cap contenidor en execució.")
            sys.exit(1)
        return container_id
    except subprocess.CalledProcessError as e:
        print(f"Error obtenint l'ID del contenidor: {e}")
        sys.exit(1)

def execute_command_in_container(container_id, command):
    try:
        subprocess.run(['docker', 'exec', '-it', container_id] + command, check=True)
        print(f"Comanda '{' '.join(command)}' executada correctament en el contenidor {container_id}")
    except subprocess.CalledProcessError as e:
        print(f"Error executant la comanda en el contenidor {container_id}: {e}")
        sys.exit(1)
        
def check_and_start_postfix(container_id):
    try:
        result = subprocess.run(['docker', 'exec', '-it', container_id, 'service', 'postfix', 'status'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode()
        if "* postfix is running" not in output:
            print("Postfix no està en funcionament. Iniciant el servei...")
            subprocess.run(['docker', 'exec', '-it', container_id, 'service', 'postfix', 'start'], check=True)
            print("Postfix s'ha iniciat correctament.")
        else:
            print("Postfix ja està en funcionament.")
    except subprocess.CalledProcessError as e:
        print(f"Error comprovant o iniciant el servei Postfix: {e}")
        sys.exit(1)
        
def setup_cron_jobs(container_id):
    cron_jobs = [
        f"*/1 * * * * docker exec -it {container_id} python3.9 /home/usuari/reports/LB-logs/lb-logs-prod.py >> /home/usuari/reports/LB-logs/logs/lb-output.log 2>> /home/usuari/reports/LB-logs/logs/lb-error.log",
        f"*/1 * * * * docker exec -it {container_id} python3.9 /home/usuari/reports/LB-logs/lb-logs-pp.py >> /home/usuari/reports/LB-logs/logs/lb-output.log 2>> /home/usuari/reports/LB-logs/logs/lb-error.log",
        f"00 8 * * 1 docker exec -it {container_id} python3.9 /home/usuari/reports/vip_report/nitro_vip.py",
        f"20 8 * * 1 docker exec -it {container_id} python3.9 /home/usuari/reports/vip_report/email_new_vips.py",
        f"20 8 * * 1 docker exec -it {container_id} python3.9 /home/usuari/reports/vip_report/email_vips.py",
        f"30 8 * * 1 docker exec -it {container_id} pwsh -f \"/home/usuari/reports/DRS/DRS-PROD.ps1\"",
        f"30 8 * * 1 docker exec -it {container_id} pwsh -f \"/home/usuari/reports/DRS/DRS-PP.ps1\"",
        f"30 8 * * 1 docker exec -it {container_id} pwsh -f \"/home/usuari/reports/DRS/DRS-PCE.ps1\"",
        f"20 9 * * 1 docker exec -it {container_id} sh /home/usuari/reports/DRS/DRS-email.sh",
        f"00 8 * * 1 docker exec -it {container_id} pwsh -f \"/home/usuari/reports/Orphaned/ORPH-PROD.ps1\"",
        f"00 8 * * 1 docker exec -it {container_id} pwsh -f \"/home/usuari/reports/Orphaned/ORPH-PP.ps1\"",
        f"00 8 * * 1 docker exec -it {container_id} pwsh -f \"/home/usuari/reports/Orphaned/ORPH-PCE.ps1\"",
        f"20 9 * * 1 docker exec -it {container_id} bash -f \"/home/usuari/reports/Orphaned/ORPH-email.sh\"",
        f"0 0 * */2 * rm /home/usuari/reports/LB-logs/logs/*"
    ]
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_crontab:
            subprocess.run(['crontab', '-l'], stdout=temp_crontab, stderr=subprocess.DEVNULL)
            with open(temp_crontab.name, 'a') as f:
                for job in cron_jobs:
                    f.write(f"{job}\n")
        subprocess.run(['crontab', temp_crontab.name], check=True)
        os.remove(temp_crontab.name)
        print("Els cron jobs s'han configurat correctament.")
    except subprocess.CalledProcessError as e:
        print(f"Error configurant els cron jobs: {e}")
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

if not check_ssh_connectivity_with_nc('gitlab.test'):
    print("No hi ha connectivitat amb gitlab.test per SSH")
    sys.exit(1)

# Clonar el repositori si hi ha connectivitat
if not clone_repository('git@github.com:marcmoiagese/pybunpwsh.git'):
    sys.exit(1)

# Comprovacions de connectivitat a altres adreces IP i ports
checks = [
    ('vcenterprod.test', 443),
    ('vcenterpre.test', 443),
    ('192.158.290.179', 22),
    ('192.158.98.37', 22)
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
citrix_password = input("Introdueix la contrasenya per l'usuari Us3R: ")
lb_pass_pp = input("Introdueix la contrasenya per l'usuari Us3R: ")
lb_pass_prod = input("Introdueix la contrasenya per l'usuari Us3R: ")

# Crear el fitxer docker-compose.override.yml amb les contrasenyes introduïdes
create_docker_compose_override_file('./pybunpwsh', citrix_password, lb_pass_pp, lb_pass_prod)

# Executar 'docker compose up -d' per iniciar els serveis
run_docker_compose_up('./pybunpwsh')

print("Totes les comprovacions han passat correctament.")

# Obtenir l'ID del contenidor més recent
container_id = get_latest_container_id()

print("!!! Prepara les credencials del vcenter de PRE referents a l'usuari Us3R ")

# Executar la comanda 'pwsh -f "/home/usuari/reports/DRS/DRS-PCE.ps1"' dins del contenidor
execute_command_in_container(container_id, ['/usr/bin/pwsh', '-f', '/home/usuari/reports/DRS/DRS-PP.ps1'])

print("!!! Prepara les credencials del vcenter de PRO referents a l'usuari Us3R ")

# Executar la comanda 'pwsh -f "/home/usuari/reports/DRS/DRS-PCE.ps1"' dins del contenidor
execute_command_in_container(container_id, ['/usr/bin/pwsh', '-f', '/home/usuari/reports/DRS/DRS-PROD.ps1'])

check_and_start_postfix(container_id)

setup_cron_jobs(container_id)

# Eliminar els fitxers residuals
if os.path.exists('./pybunpwsh'):
    try:
        shutil.rmtree('./pybunpwsh')
        print("Cleanup completed")
    except Exception as e:
        print(f"Error eliminant el directori ./pybunpwsh: {e}")
        sys.exit(1)