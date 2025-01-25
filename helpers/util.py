#!/usr/bin/env python3
""" Various utilities for oci_cn_auth """

import configparser
import subprocess
import tempfile
import filecmp
import os
import sys
import shutil
import socket
import datetime
import psutil
from jinja2 import Environment, FileSystemLoader
import OpenSSL
import time

from helpers import systemd, metadata, cert
import helpers.interfaces


class RdmaInterface():
    """ RDMA NIC object """

    def __init__(self, interface):
        self.interface = interface
        self.service = WpaSupplicantService(interface)

    @property
    def is_up(self):
        """ Check if interface is UP"""
        interfaces = psutil.net_if_stats()
        if self.interface not in interfaces:
            return False
        else:
            return interfaces[self.interface].isup

    @property
    def ips(self):
        """ Get list of IP addresses configured on the interface """
        interfaces = psutil.net_if_addrs()

        ips = []

        if self.interface not in interfaces:
            return ips

        for link in interfaces[self.interface]:
            if link.family == socket.AF_INET:
                if link.address:
                    ips.append(link.address)

        return ips


class WpaSupplicantService():
    """ Manage wpa_supplicant services and systemd units """

    def __init__(self, interface):
        self.interface = interface
        self.service = f"wpa_supplicant-wired@{interface}.service"
        self.unitfile = f"/etc/systemd/system/wpa_supplicant-wired@{interface}.service"

    def start(self):
        """ start service """
        return systemd.start(self.service)['status']

    def enable(self):
        """ enable service """
        return systemd.enable(self.service)['status']

    def stop(self):
        """ stop service """
        return systemd.stop(self.service)['status']

    def disable(self):
        """ disable service """
        return systemd.disable(self.service)['status']

    def delete(self):
        """ delete unit file """
        if os.path.isfile(self.unitfile):
            return os.remove(self.unitfile)
        else:
            return False

    def send_and_receive(self, message):
        """ communicate over socket with wpa supplicant """
        wpa_socket_file = f"/var/run/wpa_supplicant/{self.interface}"
        return_socket_file = f"/tmp/{self.interface}.socket"

        if os.path.exists(return_socket_file):
            os.remove(return_socket_file)

        if os.path.exists(wpa_socket_file):
            return_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            return_socket.bind(return_socket_file)

            return_socket.sendto(str.encode(message), wpa_socket_file)
            (byte_data, _) = return_socket.recvfrom(4096)

            reply = byte_data.decode('utf-8')
            return_socket.close()
            os.remove(return_socket_file)
        else:
            reply = ""

        return reply

    @property
    def is_authenticated(self):
        """ Check if wpa supplicant returns authenticated status """

        status = self.send_and_receive('STATUS')
        state = False

        for line in status.splitlines():
            if 'suppPortStatus' in line:
                state = line.split('=')[1]

        if state == 'Authorized':
            return True
        else:
            return False

    @property
    def dump_state(self):
        """ Check if wpa supplicant is already re-authenticating """
        status = self.send_and_receive('STATUS')
        for line in status.splitlines():
            if 'Supplicant' in line:
                print(line.split('=')[1], flush=True)
            elif 'eap_session_id' in line:
                print(line.split('=')[1], flush=True)

    def reconfigure(self):
        """ reload wpa supplicant """
        status = self.send_and_receive('RECONFIGURE')
        return status

    def reauthenticate(self):
        """ ask to reauthenticate """
        status = self.send_and_receive('REAUTHENTICATE')
        return status

    def create_unit(self, write=True):
        """ create unit file """
        template = _create_template()

        with tempfile.NamedTemporaryFile() as tmpfile:
            tmpfile = tempfile.NamedTemporaryFile(mode='w')
            tmpfile.write(template)
            tmpfile.flush()

            if os.path.isfile(self.unitfile):
                filecmp.clear_cache()
                if not filecmp.cmp(tmpfile.name, self.unitfile):
                    if write:
                        shutil.copyfile(tmpfile.name, self.unitfile)
                        tmpfile.close()
                    return True

            else:
                if write:
                    shutil.copyfile(tmpfile.name, self.unitfile)
                    tmpfile.close()
                return True

        return False

    @property
    def is_running(self):
        """ check if service is running """
        return systemd.is_active(self.service)['status']

    @property
    def is_enabled(self):
        """ check if service is enabled """
        return systemd.is_enabled(self.service)['status']


def interface_list(config):
    """ list system interfaces based on shape """
    shape = metadata.get_instance()['shape']
    if config.getboolean('DEFAULT', 'auto') is True:
        interfaces = helpers.interfaces.get_interfaces_by_shape(shape)
    else:
        interfaces = config['DEFAULT']['interfaces'].split(',')

    return interfaces


def run_command(command):
    """ Execute shell command """
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


def template_wpa_config_file(config, cluster_info, instance_metadata):
    """ template configuration file """

    directory = os.path.dirname(os.path.abspath(__file__))

    if cluster_info:
        identity_n = cluster_info + "-" + instance_metadata['id']
    else:

        try:
        # I don't remember what was the problem with getaddrinfo
        # or why we're not always using getfqdn()

            identity_n = socket.getaddrinfo(socket.gethostname(),
                                            0, flags=socket.AI_CANONNAME)[0][3] + "-" \
                         + instance_metadata['id']
        except (OSError, socket.gaierror):
            identity_n = socket.getfqdn() + "-" + instance_metadata['id']

    j2_env = Environment(loader=FileSystemLoader(directory),
                         trim_blocks=True)

    return j2_env.get_template('templates/wpa_supplicant-wired-interface.conf').render(
        private_key_passwd=config['DEFAULT']['password'],
        private_key=config['DEFAULT']['private_key'],
        identity=identity_n
    )


def create_wpa_config_file(config, cluster_info, instance_metadata):
    """ create WPA supplicant configuration file (one file for all interfaces) """

    changed = False
    instance_metadata = metadata.get_instance()
    template = template_wpa_config_file(config, cluster_info, instance_metadata)
    config_file = '/etc/wpa_supplicant/wpa_supplicant-wired-8021x.conf'

    with tempfile.NamedTemporaryFile() as tmpfile:
        tmpfile = tempfile.NamedTemporaryFile(mode='w')
        tmpfile.write(template)
        tmpfile.flush()
        if os.path.isfile(config_file):
            if not filecmp.cmp(tmpfile.name, config_file):
                print(f"Updating  {config_file}", flush=True)
                with open(config_file, 'w', encoding='utf-8') as config_file:
                    config_file.write(template)
                changed = True
        else:
            print(f"Updating {config_file}", flush=True)
            with open(config_file, 'w', encoding='utf-8') as config_file:
                config_file.write(template)
                changed = True

    return changed


def delete_wpa_config_file():
    config_file = '/etc/wpa_supplicant/wpa_supplicant-wired-8021x.conf'
    try:
        os.remove(config_file)
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f'Unable to remove wpa_supplicant config {config_file}: {e}', flush=True)
        sys.exit(1)


def _should_configure(config, interface):
    """ check if interface should be configured """
    try:
        ip_required = config.getboolean('DEFAULT', 'require_ip')

    except configparser.Error:
        ip_required = False

    if not interface.is_up:
        print(f"[ WARN ] interface {interface.interface} is DOWN", flush=True)
        return False

    if ip_required:
        if not interface.ips:
            print(f"[ WARN ] interface {interface.interface} "
                  f"has no IP address but ip_required is set to True", flush=True)
            return False

    return True


def check_units(config, interface, write=True, start=True):
    """ TODO: simplify """
    changed = False
    rdma_interface = RdmaInterface(interface)
    should_configure = _should_configure(config, rdma_interface)

    if should_configure:
        if rdma_interface.service.create_unit(write=False):
            if not write:
                print(f"Unit {rdma_interface.interface} needs updating", flush=True)
            else:
                print(f"Updating unit: {rdma_interface.interface}", flush=True)
                rdma_interface.service.create_unit()
                print('Reloading systemd', flush=True)
                systemd.reload()
                changed = True

        else:
            print(f"[ OK ] {rdma_interface.service.service}", flush=True)

        #if not rdma_interface.service.is_enabled:
        #    if start:
        #        print(f"Enabling service {rdma_interface.service.service}", flush=True)
        #        rdma_interface.service.enable()
        #    else:
        #        print(f"[ ERROR ] Service {rdma_interface.service.service} not enabled", flush=True)
        if not rdma_interface.service.is_running:
            if start:
                print(f"Starting service {rdma_interface.service.service}", flush=True)
                rdma_interface.service.start()
            else:
                print(f"[ ERROR ] Service {rdma_interface.service.service} not running", flush=True)
    else:
        if write:
            if rdma_interface.service.is_running:
                print(f"Stopping {rdma_interface.service.service}", flush=True)
                rdma_interface.service.stop()
            if rdma_interface.service.is_enabled:
                print(f"Disabling {rdma_interface.service.service}", flush=True)
                rdma_interface.service.disable()
            if os.path.isfile(rdma_interface.service.unitfile):
                print(f"Deleting {rdma_interface.service.service}", flush=True)
                rdma_interface.service.delete()

    return changed


def reload_wpa_supplicant(interface):
    """ reload configuration for wpa_supplicant over socket connection """

    wpa = WpaSupplicantService(interface)
    wpa.reconfigure()

    # for p in psutil.process_iter():
    #    pinfo = p.as_dict(attrs=['pid', 'name'])
    #    if pinfo['name'] == 'wpa_supplicant':
    #        print('Sending HUP signal to PID: {}'.format(pinfo['pid']))
    #        p.send_signal(psutil.signal.SIGHUP)


def check_configs(config, cluster_info, write=True):
    """ Check if configuration file changed / requires changing """
    instance_metadata = metadata.get_instance()

    changed = False

    if write:
        print('Checking wpa-supplicant config file', flush=True)
        changed = create_wpa_config_file(config, cluster_info, instance_metadata)

    return changed


def check_certificates(config, write=True):
    """ TODO split checking and certificate generation """

    new_bundle = None
    changed = False
    cluster_info = None
    private_key = config['DEFAULT']['private_key']

    now = datetime.datetime.now(datetime.timezone.utc)
    date_time = now.strftime("%Y-%m-%d %H:%M:%S %Z")

    try:
        identity_metadata = metadata.get_identity()
    except Exception as error:
        print(f"ERROR: Unable to get identity information", flush=True)
        msg = f'ERROR: Unable to get identity information {date_time}'
        output_to_console(msg)
        sys.exit(1)

    metadata_cert = identity_metadata['cert.pem']
    metadata_ca = identity_metadata['intermediate.pem']
    metadata_private_key = identity_metadata['key.pem']
    private_key_passwd = config['DEFAULT']['password']

    if os.path.isfile(private_key):
        try:
            with open(private_key, 'rb') as certificate_bundle:
                old_bundle = cert.CertBundle().load_from_file \
                    (certificate_bundle.read(), private_key_passwd)

        except OpenSSL.crypto.Error as error:
            print(f"WARNING: Unable to read existing certificate. Reason: {error}", flush=True)
            old_bundle = None

    else:
        print('No existing certificate.', flush=True)
        old_bundle = None

    new_cert = cert.Cert(metadata_cert)

    if not new_cert.get_san():
        if os.path.exists('/var/run/oci-cn-auth/status'):
            # oci_cn_auth previously had SAN
            print('ERROR Certificate missing SAN information', flush=True)
            msg = f'ERROR Certificate missing SAN information {date_time}'
            output_to_console(msg)
            sys.exit(1)
        else:
            # oci_cn_auth started and no SAN found
            print('Started without Certificate SAN information', flush=True)
            msg = f'Started without Certificate SAN information {date_time}'
            output_to_console(msg)
            sys.exit(0)
    else:
        # oci_cn_auth SAN found
        with open('/var/run/oci-cn-auth/status', 'w', encoding='UTF-8') as file_name:
            file_name.write('san found')
        cluster_info = new_cert.cluster_info()

    if old_bundle:
        if old_bundle.not_valid_after != new_cert.not_valid_after:
            print(
                f"current certificate valid until: {old_bundle.not_valid_after} "
                f"| next certificate valid until: {new_cert.not_valid_after}", flush=True)
            print("Certificate changed. Generating PKCS12", flush=True)
            new_bundle = cert.CertBundle().create(
                metadata_cert,
                metadata_private_key,
                private_key_passwd,
                metadata_ca
            )
        else:
            print(
                f"current certificate valid until: {old_bundle.not_valid_after} "
                f"| next certificate valid until: {new_cert.not_valid_after}", flush=True)
            print('Certificate not changed. Skipping...', flush=True)
    else:
        print(f"new certificate valid until: {new_cert.not_valid_after}", flush=True)
        print('Old bundle not found. Generating PKCS12', flush=True)
        new_bundle = cert.CertBundle().create(metadata_cert, metadata_private_key,
                                              private_key_passwd, metadata_ca)

    if new_bundle and write:
        with open(private_key, 'wb') as pkcs12:
            pkcs12.write(new_bundle.export_pkcs12())
            changed = True
        # set_selinux_attributes(private_key)

    return changed, cluster_info


def _create_template():
    """ generate systemd unit file from template """
    directory = os.path.dirname(os.path.abspath(__file__))
    j2_env = Environment(loader=FileSystemLoader(directory),
                         trim_blocks=True)
    wpa_supplicant_path = shutil.which('wpa_supplicant')
    wpa_supplicant_realpath = os.path.realpath(wpa_supplicant_path)
    return j2_env.get_template('templates/wpa_supplicant-wired@interface.service').render(
        wpa_supplicant=wpa_supplicant_realpath)


def delete_certificate(config):
    """ delete PKCS12 bundle """
    private_key = config['DEFAULT']['private_key']
    try:
        os.remove(private_key)
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f'Unable to remove certificate {private_key}: {e}', flush=True)
        sys.exit(1)

def stat_certificate(config):
    """ stat PKCS12 bundle """
    private_key = config['DEFAULT']['private_key']
    start_window = (60*60) - 90
    stop_window = (60*60) + 90
    try:
        mtime = os.path.getmtime(private_key)
    except OSError:
        mtime = 0
        pass
    current_time = time.time()
    print(f"stat: {current_time} {mtime}", flush=True)
    if (current_time > (mtime + start_window)) and (current_time < (mtime + stop_window)):
        return True
    return False

def output_to_console(msg):
    try:
        with open('/dev/console', 'w') as f:
            f.write(msg)
    except OSError as e:
        print(f'Unable to write to /dev/console: {e}', flush=True)


def set_selinux_attributes(filename):
    chcon = shutil.which('chcon')
    command = [chcon, 'system_u:object_r:etc_t:s0', filename]
    result = run_command(command)
    if result['status'] is False:
        print(f'Unable to set attributes: {filename}', flush=True)
