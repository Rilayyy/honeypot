from logging.handlers import RotatingFileHandler
import logging
import socket
import paramiko
import threading
#CONSTANTS
SSH_BANNER = 'SSH-2.0-MySShServer_1.0'
logging_format = logging.Formatter('%(message)s')
host_key = 'server.key'

# logger and logging files
# Logs connection attempts
funnel_logger = logging.getLogger('FunnelLogger')
funnel_logger.setLevel(logging.INFO)
funnel_handler = RotatingFileHandler('audit.log', maxBytes=2000, backupCount=5)
funnel_handler.setFormatter(logging_format)
funnel_logger.addHandler(funnel_handler)

# Logs commands send to the shell
creds_logger = logging.getLogger('CredsLogger')
creds_logger.setLevel(logging.INFO)
creds_handler = RotatingFileHandler('cmd_audit.log', maxBytes=2000, backupCount=5)
creds_handler.setFormatter(logging_format)
creds_logger.addHandler(creds_handler)

# emulated shell
def emulated_shell(channel, client_ip):
    channel.send(b'Riley$ ')
    command = b''
    while True:
        char = channel.recv(1)
        channel.send(char)
        if not char:
            channel.close()

        command += char

        if char == b'\r':
            if command.strip() == b'exit':
                response = b'\n Goodbye \n'
                channel.close()
            elif command.strip() == b'pwd':
                response = b'\n' b'\\usr\\local' + b'\r\n'
            elif command.strip() == b'whoami':
                response = b'\n' + b'riley' + b'\r\n'
            elif command.strip() == b'ls':
                response = b'\n' + b'jumpbox1.conf' + b'\r\n'
            elif command.strip() == b'cat jumpbox1.conf':
                response = b'\n' + b'Go to deeboodag.com' + b'\r\n'
            else:
                response = b'\n' + bytes(command.strip()) + b'\r\n'



class Server(paramiko.ServerInterface):

    # Store IP, username, password
    def __init__(self,client_ip,input_username=None, input_password=None):
        self.client_ip = client_ip
        self.input_username = input_username
        self.input_password = input_password

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED

    def get_allowed_auths(self):
        return 'password'

    def check_auth_password(self, username, password):
        if self.input_username is not None and self.input_password is not None:
            return paramiko.AUTH_SUCCESSFUL

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    def check_channel_exec_request(self, channel, command):
        command = str(command)
        return True


def client_handle(client, addr, username, password):
    client_ip = addr[0]
    print(f'{client_ip} has connected to the server.')

    try:
        transport = paramiko.Transport()
        transport.local_version = SSH_BANNER # Fake SSH banner
        server = Server(client_ip=client_ip, input_username=username, input_password=password)

        transport.add_server_key(host_key) # Adds host key

        transport.start_server(server=server)

        # Accepts SSH channel and welcomes user
        channel = transport.accept(100)
        if channel is None:
            print("No channel was opened")

        standard_banner = "Welcome to Ubuntu \r\r\r\n"
        channel.send(standard_banner)
        emulated_shell(channel,client_ip=client_ip) # Launches emulated shell
    except Exception as error:
        print(error)
        print("!!ERROR!!")
    finally:
        try:
            transport.close()
        except Exception as error:
            print(error)
            print("!!!ERROR!!!")
        client.close()

def honeypot(address, port, username, password):
    socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socks.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socks.bind((address, port))

    socks.listen(100)
    print(f'SSH server is listening on port {port}')

    while True:
        try:
            client, addr = socks.accept()

        except Exception as error:
            print(error)

        



