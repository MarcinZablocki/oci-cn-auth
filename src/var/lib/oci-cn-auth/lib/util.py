#!/usr/bin/env python3

import psutil
import subprocess
import tempfile
from jinja2 import Environment, FileSystemLoader
import filecmp
import os
import shutil
import socket
import OpenSSL
import lib.interfaces
import lib.cert
import lib.systemd
import lib.metadata

class RdmaInterface(object): 
    def __init__(self, interface): 
        self.interface = interface
        self.service = WpaSupplicantService(interface)

    @property
    def is_up(self): 
        interfaces = psutil.net_if_stats()
        if self.interface not in interfaces:
            return False
        else:
            return interfaces[self.interface].isup

    @property
    def ips(self): 
        interfaces = psutil.net_if_addrs()

        ips = []

        if self.interface not in interfaces: 
            return ips

        for link in interfaces[self.interface]:
            if link.family == socket.AF_INET:
                if link.address:
                    ips.append(link.address)

        return ips
        
class WpaSupplicantService(object):
    def __init__(self, interface): 
        self.interface = interface
        self.service = 'wpa_supplicant-wired@{}.service'.format(interface)
        self.unitfile = '/etc/systemd/system/wpa_supplicant-wired@{}.service'.format(interface)
        
    def start(self): 
        return lib.systemd.start(self.service)['status']

    def enable(self): 
        return lib.systemd.enable(self.service)['status']

    def stop(self): 
        return lib.systemd.stop(self.service)['status']

    def disable(self): 
        return lib.systemd.disable(self.service)['status']

    def delete(self): 
        if os.path.isfile(self.unitfile): 
            return os.remove(self.unitfile)
        else: 
            return False

    def template(self):
        directory = os.path.dirname(os.path.abspath(__file__))
        j2_env = Environment(loader=FileSystemLoader(directory),
            trim_blocks=True)
        wpa_supplicant_path = shutil.which('wpa_supplicant')
        return j2_env.get_template('templates/wpa_supplicant-wired@interface.service').render(
            wpa_supplicant=wpa_supplicant_path)

    def create_unit(self, write=True):
        
        template = self.template()

        with tempfile.NamedTemporaryFile() as tmpfile:   
            tmpfile = tempfile.NamedTemporaryFile(mode='w')
            tmpfile.write(template)
            tmpfile.flush()

            if os.path.isfile(self.unitfile):

                if not filecmp.cmp(tmpfile.name, self.unitfile):
                    
                    if write: 
                        shutil.copyfile(tmpfile.name, self.unitfile)
                        tmpfile.close()

                    return True
                    
            else:
                
                if write: 
                    shutil.copyfile(tmpfile.name, self.unitfile)

                return True

        return False

    @property
    def is_running(self): 
        return lib.systemd.is_active(self.service)['status']

    @property
    def is_enabled(self): 
        return lib.systemd.is_enabled(self.service)['status']

def _interfaces(config): 
    shape = lib.metadata.get_instance()['shape']
    print
    if config.getboolean('DEFAULT', 'auto') is True: 
        interfaces = lib.interfaces.get_interfaces_by_shape(shape)

    else: 
        interfaces = config['DEFAULT']['interfaces'].split(',')

    return interfaces

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

    try: 
        identity_n=socket.getaddrinfo(socket.gethostname(), 0, flags=socket.AI_CANONNAME)[0][3]+"-"+instance_metadata['id']
    except (OSError, socket.gaierror):
        identity_n=socket.getfqdn()+"-"+instance_metadata['id']
    
    j2_env = Environment(loader=FileSystemLoader(directory),
        trim_blocks=True)

    return j2_env.get_template('templates/wpa_supplicant-wired-interface.conf').render(
        private_key_passwd=config['DEFAULT']['password'],
        private_key=config['DEFAULT']['private_key'],
        identity=identity_n
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

def _should_configure(config, interface): 
    
    try: 
        ip_required = config.getboolean('DEFAULT', 'require_ip')

    except:
        ip_required  = False

    if not interface.is_up:
        print('[ WARN ] interface {} is DOWN'.format(interface.interface))
        return False

    if ip_required: 
        if not interface.ips: 
            print('[ WARN ] interface {} has no IP address but ip_required is set to True'.format(interface.interface))
            return False
            
    return True 

def check_units(config, write=True, start=True): 
    system_interfaces = _interfaces(config)

    for i in system_interfaces: 
        interface = RdmaInterface(i)
        should_configure = _should_configure(config, interface)
        
        if should_configure:
            if interface.service.create_unit(write=False):
                if not write:
                  print('Unit {} needs updating'.format(interface.interface))
                else:
                  print('Updating unit: {}'.format(interface.interface))
                interface.service.create_unit()
                if write:
                  print('Reloading systemd')
                  lib.systemd.reload()

            else: 
                print('[ OK ] {}'.format(interface.service.service))

            if not interface.service.is_enabled:
                if start: 
                    print('Enabling service {}'.format(interface.service.service))
                    interface.service.enable()
                else: 
                    print('[ ERROR ] Service {} not enabled'.format(interface.service.service))
            if not interface.service.is_running: 
                if start: 
                    print('Staring service {}'.format(interface.service.service))
                    interface.service.start()
                else: 
                    print('[ ERROR ] Service {} not running'.format(interface.service.service))
        else: 
            if write:
                if interface.service.is_running:
                    print('Stopping {}'.format(interface.service.service)) 
                    interface.service.stop()
                if interface.service.is_enabled:
                    print('Disabling {}'.format(interface.service.service)) 
                    interface.service.disable()

                if os.path.isfile(interface.service.unitfile): 
                    print('Deleting {}'.format(interface.service.service))
                    interface.service.delete()
                
def reload_wpa_supplicant(): 
    for p in psutil.process_iter():
        pinfo = p.as_dict(attrs=['pid', 'name'])
        if pinfo['name'] == 'wpa_supplicant':
            print('Sending HUP signal to PID: {}'.format(pinfo['pid']))
            p.send_signal(psutil.signal.SIGHUP)


def check_configs(config, write=True):
    instance_metadata = lib.metadata.get_instance()
    
    changed = False

    if write: 
        print('Checking wpa-supplicant config file')
        changed = create_wpa_config_file(config, instance_metadata)
    
    if not changed: 
        print('[ OK ] WPA Supplicant configuration')
                       
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
        print("Reloading WPA Supplicant")
        reload_wpa_supplicant()
