#!/usr/bin/env python3

import psutil
import subprocess
import tempfile
import lib.cert
import lib.systemd
import lib.metadata
from jinja2 import Environment, FileSystemLoader
import filecmp
import os
import shutil
import socket
import OpenSSL

def run_command(command):
    """ Execute systemd command """
    result = {}
    process = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    exit_code = process.wait()

    result['exit_code'] = exit_code
    result['sdout'] = process.stdout

    if exit_code == 0:
        result['status'] = True
    else: 
        result['status'] = False

    return result


def template_wpa_config_file(config, instance_metadata):
    directory = os.path.dirname(os.path.abspath(__file__))
    
    j2_env = Environment(loader=FileSystemLoader(directory),
        trim_blocks=True)

    return j2_env.get_template('templates/wpa_supplicant-wired-interface.conf').render(
        private_key_passwd=config['DEFAULT']['password'],
        private_key=config['DEFAULT']['private_key'],
        identity=socket.getaddrinfo(socket.gethostname(), 0, flags=socket.AI_CANONNAME)[0][3]+"-"+instance_metadata['id']
    )

def create_wpa_config_file(config, instance_metadata):
    changed = False
    instance_metadata = lib.metadata.get_instance()
    template = template_wpa_config_file(config, instance_metadata)
    config_file = '/etc/wpa_supplicant/wpa_supplicant-wired-8021x.conf'

    with tempfile.NamedTemporaryFile() as tmpfile:   
        tmpfile = tempfile.NamedTemporaryFile(mode='w')
        tmpfile.write(template)
        tmpfile.flush()
        if os.path.isfile(config_file): 
            if not filecmp.cmp(tmpfile.name, config_file):
                print('Updating  {}'.format(config_file))
                with open(config_file, 'w') as cf:
                    cf.write(template)
                changed = True
        else: 
            print('Updating {}'.format(config_file))
            with open(config_file, 'w') as cf:
                cf.write(template)               
                changed = True
    
    return changed

def template_wpa_unit_file(interface):

    directory = os.path.dirname(os.path.abspath(__file__))
    j2_env = Environment(loader=FileSystemLoader(directory),
        trim_blocks=True)
    
    return j2_env.get_template('templates/wpa_supplicant-wired@interface.service').render()

def create_unit(interface, write):
    unitfile = '/etc/systemd/system/wpa_supplicant-wired@{}.service'.format(interface)
    template = template_wpa_unit_file(interface)

    with tempfile.NamedTemporaryFile() as tmpfile:   
        tmpfile = tempfile.NamedTemporaryFile(mode='w')
        tmpfile.write(template)
        tmpfile.flush()

        if os.path.isfile(unitfile):

            if not filecmp.cmp(tmpfile.name, unitfile):

                if write: 
                    print('Writing template for {}'.format(unitfile))
                    shutil.copyfile(tmpfile.name, unitfile)
                    tmpfile.close()

                return True
                
        else:
            if write: 
                shutil.copyfile(tmpfile.name, unitfile)

            return True

    return False
    
def check_units(config, write=True, start=True): 

    """ Checks if systemd unit files exist for configured interfaces """

    changed = {}

    interfaces = config['DEFAULT']['interfaces'].split(',')
    system_interfaces = psutil.net_if_stats()

    for interface in interfaces: 

        if interface not in system_interfaces:
            print('Interface {} not found'.format(interface))
            continue

        else: 

            service = 'wpa_supplicant-wired@{}'.format(interface)
            #enabled = lib.systemd.is_enabled(service)

            changed[interface] = create_unit(interface,write)
            if changed[interface]: 
                print('Interface {} requires configuration'.format(interface))
            else: 
                print('Interface {} configured properly'.format(interface))
            
    if start: 
        print('Reloading systemd')
        lib.systemd.reload()

    for interface in changed: 
        if start: 
            if interface in system_interfaces: 

                service = 'wpa_supplicant-wired@{}'.format(interface)

                if system_interfaces[interface].isup: 
                    if not lib.systemd.is_active(service):
                        
                        print('Enabling systemd service {}'.format(service))
                        lib.systemd.enable(service)

                else: 
                    print('Interface {} down'.format(interface))
                    continue
            else: 
                print('Interface {} not found'.format(interface))

    if start: 
        for interface in interfaces: 
            service = 'wpa_supplicant-wired@{}'.format(interface)
            active = lib.systemd.is_active(service)
                
            if active['status']: 
                print('Service {} is running'.format(service))
            else: 
                if interface in system_interfaces: 
                    if system_interfaces[interface].isup: 
                        print('Starting service {}'.format(service))
                        lib.systemd.start(service)
                    else: 
                        continue

                else: 
                    continue

def reload_wpa_supplicant(): 
    for p in psutil.process_iter(['name']):
        if p.info['name'] == 'wpa_supplicant':
            print('Sending HUP signal to PID: {}'.format(p.pid))
            p.send_signal(psutil.signal.SIGHUP)

def check_configs(config, write=True):
    instance_metadata = lib.metadata.get_instance()
    
    changed = False

    if write: 
        print('Creating wpa-supplicant config file')
        changed = create_wpa_config_file(config, instance_metadata)
                       
    if changed and write: 
        print('Configuration changed reloading WPA supplicant')
        reload_wpa_supplicant()

def check_certificates(config, write=True): 
    new_bundle = None
    changed = False
    private_key = config['DEFAULT']['private_key']

    identity_metadata = lib.metadata.get_identity()

    metadata_cert = identity_metadata['cert.pem']
    metadata_ca = identity_metadata['intermediate.pem']
    metadata_private_key = identity_metadata['key.pem']
    private_key_passwd = config['DEFAULT']['password']

    if os.path.isfile(private_key):
        try:
            with open(private_key, 'rb') as b:
                old_bundle = lib.cert.LoadBundle(b.read(), private_key_passwd)
        except OpenSSL.crypto.Error:
            print('WARNING: Unable to read existing certificate.')
            old_bundle = None
    else:
        print('No existing certificate.')
        old_bundle = None

    new_cert = lib.cert.Cert(metadata_cert)

    if not new_cert.get_san():
        raise ValueError('Certificate missing SAN information. Not valid for Cluster Networking')
    
    if old_bundle: 
        if not old_bundle.not_valid_after == new_cert.not_valid_after:
            print("old certificate valid until: {} | new certificate valid until: {}".format(old_bundle.not_valid_after, new_cert.not_valid_after))
            print('Certificate changed. Generating PKCS12')
            new_bundle = lib.cert.NewBundle(metadata_cert, metadata_private_key, private_key_passwd, metadata_ca)
        else: 
            print("old certificate valid until: {} | new certificate valid until: {}".format(old_bundle.not_valid_after, new_cert.not_valid_after))
            print('Certificate not changed. Skipping...')
    else: 
        print("new certificate valid until: {}".format(new_cert.not_valid_after))
        print('Old bundle not found. Generating PKCS12')
        new_bundle = lib.cert.NewBundle(metadata_cert, metadata_private_key, private_key_passwd, metadata_ca)
        

    if new_bundle and write: 
        with open(private_key, 'wb') as pkcs12:
            pkcs12.write(new_bundle.export_pkcs12())
            changed = True

    if changed and write: 
        reload_wpa_supplicant()