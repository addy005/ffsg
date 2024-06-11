import argparse
import json
import os
import psutil
import signal
import socket
import sys
import subprocess
from multiprocessing import Process
import time

def get_saved_data():
    try:
        with open('data.json', 'r') as file:
            data = json.load(file)
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def save_data(data):
    with open('data.json', 'w') as file:
        json.dump(data, file)

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def find_and_terminate_process(port):
    for process in psutil.process_iter(['pid', 'name', 'connections']):
        for conn in process.info.get('connections', []):
            if conn.laddr.port == port:
                print(f"Port {port} is in use by process {process.info['name']} (PID {process.info['pid']})")
                try:
                    process.terminate()
                    print(f"Terminated process with PID {process.info['pid']}")
                except psutil.NoSuchProcess:
                    print(f"Process with PID {process.info['pid']} not found")

def run_app(env):
    cmd = 'python run.py --execution-providers cuda > log.txt & ssh -o StrictHostKeyChecking=no -p 80 -R0:localhost:7860 a.pinggy.io > log.txt'
    subprocess.run(cmd, shell=True, env=env)

def print_url():
    print("waiting for output")
    time.sleep(2)
    sys.stdout.flush()

    found = False
    with open('log.txt', 'r') as file:
        end_word = '.pinggy.link'
        for line in file:
            start_index = line.find("http:")
            if start_index != -1:
                end_index = line.find(end_word, start_index)
                if end_index != -1:
                    print("😁 😁 😁")
                    print("URL: " + line[start_index:end_index + len(end_word)])
                    print("😁 😁 😁")
                    found = True
    if not found:
        print_url()
    else:
        with open('log.txt', 'r') as file:
            for line in file:
                print(line)

def setup_serveo(env, target_port):
    cmd = f"ssh -R 80:localhost:{target_port} serveo.net"
    subprocess.run(cmd, shell=True, env=env)

def setup_pinggy(env):
    try:
        subprocess.check_output(['ssh', '-V'])
    except subprocess.CalledProcessError:
        subprocess.run('conda install openssh -y', shell=True, env=env)

    subprocess.run('touch log.txt', shell=True, env=env)
    open('log.txt', 'w').close()
    p_app = Process(target=run_app, args=(env,))
    p_url = Process(target=print_url)
    p_app.start()
    p_url.start()
    p_app.join()
    p_url.join()

def main():
    target_port = 7860
    env = os.environ.copy()

    if is_port_in_use(target_port):
        find_and_terminate_process(target_port)
    else:
        print(f"Port {target_port} is free.")

    parser = argparse.ArgumentParser(description='Console app with tunnel options')
    parser.add_argument('--tunnel', help='Select the tunnel [1, 2]')
    parser.add_argument('--reset', action='store_true', help='Reset saved data')

    args = parser.parse_args()

    saved_data = get_saved_data()

    if args.reset:
        if saved_data is not None:
            saved_data = { 'tunnel': ''}
    else:
        if saved_data is not None:
            if args.tunnel:
                saved_data['tunnel'] = args.tunnel 
            try: 
                print("Tunnel in the json file is: " + saved_data['tunnel'])
            except:
                saved_data['tunnel'] = ''
        else:
            saved_data = { 'tunnel': ''}

    if args.tunnel is None:
        if saved_data and saved_data['tunnel']: 
            args.tunnel = saved_data['tunnel']
        else: 
            args.tunnel = input('Enter a tunnel: pinggy [1], serveo [2] (1/2): ')
            if args.tunnel == '':
                args.tunnel = 1
            saved_data['tunnel'] = args.tunnel
            
    save_data(saved_data)

    cmd = 'python run.py --execution-providers cuda'
    
    print("Tunnel: " + args.tunnel)
    if args.tunnel == '1':
        setup_pinggy(env)
    elif args.tunnel == '2':
        setup_serveo(env, target_port)
    else:
        print('Invalid tunnel option. Please choose either 1 or 2.')

if __name__ == '__main__':
    main()
