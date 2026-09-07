import paramiko
import os
import sys
from dotenv import load_dotenv

from paths import resource_path
from pyhocon import ConfigFactory
from pyhocon.exceptions import ConfigMissingException

CONFIG_PATH = resource_path("deployctl.conf")

def load_config():
    # load the config
    try:
        config = ConfigFactory.parse_file(str(CONFIG_PATH))
    except FileNotFoundError:
        # no config file with path provided
        print(f"Configuration file not found at {CONFIG_PATH}. Please create the configuration file.")
        return None

    try:
        project_name = config.get('core.project_name')
        email = config.get('core.email_address')
        domain = config.get('web.domain')
        nginx_config_filename = config.get('web.nginx_config_filename')
    except ConfigMissingException:
        # missing keys in the config file
        print("Configuration file is missing required keys. Please check the configuration file.")
        return None

    return email, domain, nginx_config_filename, project_name

def establish_ssh_connection():
    ssh_client = paramiko.SSHClient()

    load_dotenv()
    VPS_IP = os.getenv('VPS_IP')
    VPS_USER = os.getenv('VPS_USER')
    VPS_PASSWORD = os.getenv('VPS_PASSWORD')

    if not VPS_IP:
        print("VPS IP is missing from environment variables. Please add it.")
        return False
    if not VPS_USER:
        print("VPS user is missing from environment variables. Please add it.")
        return False
    if not VPS_PASSWORD:
        print("VPS password is missing from environment variables. Please add it.")
        return False

    # validation
    ssh_client.load_system_host_keys()
    ssh_client.set_missing_host_key_policy(paramiko.RejectPolicy())

    # connection
    # port for SSH is 22
    try:
        ssh_client.connect(hostname=VPS_IP, port=22, username=VPS_USER, password=VPS_PASSWORD)
    except Exception as e:
        print(f"An error has occurred: {e}")
        return False

    return ssh_client

# helper
def run_remote(client, cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    if exit_status != 0:
        print(stdout.read().decode())
        print(stderr.read().decode())
        return False
    return True

def nginx_conf():
    # get nginx config filename
    loaded = load_config()
    if loaded is None:
        return False
    email, domain, nginx_config_filename, project_name = loaded

    # assume nginx.conf is in root
    nginx_config_path = resource_path(nginx_config_filename)
    if not nginx_config_path.exists():
        print("Nginx config cannot be found. Please create one in the root of the project.")
        return False

    if nginx_config_path.stat().st_size == 0:
        print("Nginx config is empty, you must write content in it")
        return False

    # sftp
    client = establish_ssh_connection()
    if not client:
        print("An error occurred establish an SSH connection")
        return False

    sftp = client.open_sftp()
    sftp.put(str(nginx_config_path), f"/tmp/{project_name}.conf")
    sftp.close()

    if not run_remote(client, f"sudo mv /tmp/{project_name}.conf /etc/nginx/sites-available/{project_name}"):
        print("An error occurred moving the Nginx config")
        return False
    
    # symlink
    symlink_cmd = f"sudo ln -sf /etc/nginx/sites-available/{project_name} /etc/nginx/sites-enabled/{project_name}"
    if not run_remote(client, symlink_cmd):
        return False

    # verify config
    if not run_remote(client, "sudo nginx -t"):
        print("Nginx config is invalid, please verify the config")
        return False

    # reload nginx
    if not run_remote(client, "sudo systemctl reload nginx"):
        return False

    return True

def ssl_certs():
    loaded = load_config()
    if loaded is None:
        return False
    email, domain, nginx_config_filename, project_name = loaded

    if not email:
        print("Email was not able to be retrieved, check the config file")
        return False
    if not domain:
        print("Domain was not able to be retrieved, check the config file")
        return False
    
    client = establish_ssh_connection()
    if not client:
        print("An error occurred establishing the SSH connection")
        return False

    certbot_cmd = 'sudo apt install certbot python3-certbot-nginx -y'
    ssl_gen_cmd = f'sudo certbot --nginx -d {domain} --non-interactive --agree-tos -m {email}'

    # install cerbot then create the ssl certs
    if not run_remote(client, certbot_cmd):
        print("An error occurred installing certbot")
        return False

    # issue with creating ssl cert
    if not run_remote(client, ssl_gen_cmd):
        print("An error occurred generating the SSL certificate")
        return False

    return True
    
if __name__ == "__main__":
    connection = establish_ssh_connection()
    if connection:
        print("SSH connection established successfully")

    nginx = nginx_conf()
    if nginx:
        print("Nginx configuration has been added")
    else:
        sys.exit(1)

    certgen = ssl_certs()
    if certgen:
        print("SSL certificate generates successfully")