import paramiko
import os
from dotenv import load_dotenv

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

if __name__ == "__main__":
    connection = establish_ssh_connection()
    if connection:
        print("SSH connection established successfully")