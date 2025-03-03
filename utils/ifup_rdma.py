#!/usr/bin/python3
""" Script to set up the MLX configuration for the RDMA NICs"""
#
# This script will run necessary operations for ROCE interface configuration
#

import shutil
import argparse
import os
import subprocess
import sys
import configparser

sys.path.append("/opt/oci-hpc/oci-cn-auth/")
from helpers.config import SHAPES, GPU_SHAPES, HPC_SHAPES
from helpers.metadata import get_metadata

config = configparser.ConfigParser()
CONFIG_FILE = "/etc/rdma/oracle_rdma.conf"

config.sections()
config.read(CONFIG_FILE)

FLOWCTL_TYPE = "PFC"
MTU = "4220"
DSCP_IP_VALUE = "00"
DSCP_RDMA_VALUE = "26"
DSCP_GPU_VALUE = "10"
DSCP_CNP_VALUE = "46"
RDMA_DSCP_ECN_TOS_VALUE = "105"
GPU_DSCP_ECN_TOS_VALUE = "41"
DSCP_IP_TC = "1"
DSCP_RDMA_TC = "5"
DSCP_GPU_TC = "0"
DSCP_CNP_TC = "6"

prio_0 = ["07", "06", "05", "04", "03", "02", "01", "00"]
prio_1 = ["15", "14", "13", "12", "11", "10", "09", "08"]
prio_2 = ["23", "22", "21", "20", "19", "18", "17", "16"]
prio_3 = ["31", "30", "29", "28", "27", "26", "25", "24"]
prio_4 = ["39", "38", "37", "36", "35", "34", "33", "32"]
prio_5 = ["47", "46", "45", "44", "43", "42", "41", "40"]
prio_6 = ["55", "54", "53", "52", "51", "50", "49", "48"]
prio_7 = ["63", "62", "61", "60", "59", "58", "57", "56"]

MLNX_DSCP = prio_0 + prio_1 + prio_2 + prio_3 + prio_4 + prio_5 + prio_6 + prio_7


def run_command(command):
    """ Execute systemd command """
    result = {}
    process = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    exit_code = process.wait()

    result['exit_code'] = exit_code
    result['stdout'] = process.stdout
    result['stderr'] = process.stderr

    if exit_code == 0:
        result['status'] = True
    else:
        result['status'] = False

    return result


def get_interface_pci_id(name):
    with open('/sys/class/net/{}/device/uevent'.format(name), 'r') as f:
        for line in f.readlines():
            if 'PCI_SLOT_NAME' in line:
                slot = line.split('=')[1]

    return slot


def get_interfaces(shape):
    interfaces = {}
    ids = SHAPES[shape]
    for id in ids:
        name = get_dev_name_by_id(id)
        interfaces[name] = id

    return interfaces


def get_dev_name_by_id(id):
    """ This assumes there are no virtual interfaces """
    base_path = '/sys/bus/pci/devices/{}/net/'.format(id)
    interface_name = os.listdir(base_path)[0]
    return interface_name


def get_ib_name_by_dev(dev):
    base_path = '/sys/class/net/{}/device/infiniband/'.format(dev)
    if os.path.isdir(base_path):
        ib_name = os.listdir(base_path)[0]
        return ib_name

    return None


def get_identity():
    return get_metadata('identity')


def get_instance():
    return get_metadata('instance')


def set_dscp_to_prio(interface, dscp, tc):
    command = [mlnx_qos, '-i', interface, '--dscp2prio', 'set,{},{}'.format(dscp, tc)]
    result = run_command(command)
    return result


def purge_dscp(interface, content):
    for dscp in MLNX_DSCP:
        for l in content:
            line = l.decode('utf-8')
            if 'prio:' in line:
                if dscp in line:
                    if dscp == DSCP_IP_VALUE or dscp == DSCP_RDMA_VALUE \
                            or dscp == DSCP_CNP_VALUE or dscp == DSCP_GPU_VALUE:
                        continue
                prio = line.split(':')[1][0]

                # print('prio: {}'.format(prio))

                command = [mlnx_qos, '-i', interface, '--dscp2prio', 'del,{},{}'.format(dscp, prio)]

                # print(command)

                run_command(command)

                # print(result['stdout'].read().decode('utf-8'))
    return


### CODE BELOW ###

if not os.geteuid() == 0:
    print('This utility needs to run as root')
    sys.exit(-1)

fail = False

parser = argparse.ArgumentParser(description='configure mellanox interface')
parser.add_argument('interface')

args = parser.parse_args()
interface = args.interface

if not interface:
    print('no interface set')
    sys.exit(-1)

mlxreg = shutil.which('mlxreg')
if not mlxreg:
    mlxreg = shutil.which('mstreg')

mst = shutil.which('mst')
mlnx_qos = shutil.which('mlnx_qos')
cma_roce_mode = shutil.which('cma_roce_mode')
cma_roce_tos = shutil.which('cma_roce_tos')
oci_cn_auth = "/opt/oci-hpc/oci-cn-auth/oci_cn_auth"
ibdev2netdev = shutil.which('ibdev2netdev')
sysctl = shutil.which('sysctl')
systemctl = shutil.which('systemctl')

shape = get_instance()['shape']
interfaces = get_interfaces(shape)

if shape not in SHAPES:
    print('Unknown shape {}'.format(shape))
    sys.exit(-1)

try:
    qos = config.get('QOS', 'priority')
except:
    qos = "default"

if qos == "default":

    """ read metadata and set the default priority based on shape """

    if shape in GPU_SHAPES:
        DSCP = DSCP_GPU_VALUE
        TC = GPU_DSCP_ECN_TOS_VALUE
    else:
        DSCP = DSCP_RDMA_VALUE
        TC = RDMA_DSCP_ECN_TOS_VALUE

else:

    if config.get('QOS', 'priority') == 0:
        DSCP = DSCP_GPU_VALUE
        TC = GPU_DSCP_ECN_TOS_VALUE

    else:
        DSCP = DSCP_RDMA_VALUE
        TC = RDMA_DSCP_ECN_TOS_VALUE

if not interface in interfaces:
    print('Interface {} is not a valid RDMA interface. Skipping configuration.'.format(interface))
    sys.exit(0)

mlnx_interface = get_ib_name_by_dev(interface)

if not mlnx_interface:
    print('Could not find IB name for {}'.format(interface))
    sys.exit(0)
else:
    print('{} : {}'.format(interface, mlnx_interface))

if not ibdev2netdev:
    print('Required ibdev2netdev not found on the system')
    fail = True

if not mlnx_qos:
    print('Required Mellanox utility mlnx_qos not found on the system')
    fail = True

if not cma_roce_mode:
    print('Required Mellanox utility cma_roce_mode not found on the system')
    fail = True

if not cma_roce_tos:
    print('Required Mellanox utility cma_roce_tos not found on the system')
    fail = True

if not oci_cn_auth:
    print('Required oci_cn_auth found on the system')
    fail = True

# if fail:
#    sys.exit(1)

#
# Disable autonegotiation
#
ethtool = shutil.which('ethtool')

set_autoneg_off = [ethtool, '-A', interface, 'autoneg', 'off', 'rx', 'off', 'tx', 'off']
result = run_command(set_autoneg_off)

if result['exit_code'] == 1:
    print('Error running {}.\n{}'.format(str(set_autoneg_off).join(','),
                                         result['stderr'].read().decode('utf-8')))
    sys.exit(1)

set_ring = [ethtool, '-G', interface, 'rx', '8192', 'tx', '8192']
result = run_command(set_ring)

if result['exit_code'] == 1:
    print('Error running {}.\n{}'.format(str(set_ring).join(','),
                                         result['stderr'].read().decode('utf-8')))
    sys.exit(1)

if shape in HPC_SHAPES:
    # set 18 combined channels
    set_channels = [ethtool, '-L', interface, 'combined', '18']

if shape in GPU_SHAPES:
    # set channels to combined 8
    set_channels = [ethtool, '-L', interface, 'combined', '8']

    # increase buffers and retransmission handling

    slot = get_interface_pci_id(interface)
    roce_adp_retrans_en = [mlxreg, '--yes', '-d', slot,
                           '--reg_name', 'ROCE_ACCL', '--set', 'roce_adp_retrans_en=1']
    result = run_command(roce_adp_retrans_en)

    roce_tx_window_en = [mlxreg, '--yes', '-d', slot,
                         '--reg_name', 'ROCE_ACCL', '--set', 'roce_tx_window_en=1']
    result = run_command(roce_tx_window_en)

    roce_slow_restart_en = [mlxreg, '--yes', '-d', slot,
                            '--reg_name', 'ROCE_ACCL', '--set', 'roce_slow_restart_en=1']
    result = run_command(roce_slow_restart_en)

    set_buffer = [mlnx_qos, '-i', interface, '--buffer_size=32768,229120,0,0,0,0,0,0']
    result = run_command(set_buffer)

result = run_command(set_channels)

ip = shutil.which('ip')
if not ip:
    ifconfig = shutil.which('ifconfig')

if not ip and not ifconfig:
    print('Unable to find "ip" or "ifconfig" commands')
    sys.exit(1)

if ip:
    command = [ip, 'link', 'set', 'dev', interface, 'mtu', MTU]
    result = run_command(command)
elif ifconfig:
    command = [ifconfig, interface, 'mtu', MTU]
    result = run_command(command)

if result['exit_code'] != 0:
    print('Error running {}.\n{}'.format(str(command).join(','),
                                         result['stderr'].read().decode('utf-8')))
    sys.exit(1)

if ip:
    command = [ip, 'link', 'set', 'dev', interface, 'txqueuelen', '20000']
    result = run_command(command)
elif ifconfig:
    command = [ifconfig, interface, 'txqueuelen', '20000']
    result = run_command(command)

if result['exit_code'] != 0:
    print('Error running {}.\n{}'.format(str(command).join(','),
                                         result['stderr'].read().decode('utf-8')))
    sys.exit(1)

command = [mlnx_qos, '-i', interface, '--trust dscp']
result = run_command(command)

info = [mlnx_qos, '-i', interface]
result = run_command(info)
content = result['stdout'].readlines()

purge_dscp(interface, content)
set_dscp_to_prio(interface, DSCP_IP_VALUE, DSCP_IP_TC)
set_dscp_to_prio(interface, DSCP_RDMA_VALUE, DSCP_RDMA_TC)
set_dscp_to_prio(interface, DSCP_GPU_VALUE, DSCP_GPU_TC)
set_dscp_to_prio(interface, DSCP_CNP_VALUE, DSCP_CNP_TC)

set_pfc = [mlnx_qos, '-i', interface, '--pfc', '1,0,0,0,0,1,0,0']
run_command(set_pfc)

set_prio2buffer = [mlnx_qos, '-i', interface, '--prio2buffer', '1,0,0,0,0,1,0,0']
run_command(set_prio2buffer)

set_priority_to_tc = [mlnx_qos, '-i', interface, '-p', '0,1,2,3,4,5,6,7']
run_command(set_priority_to_tc)

set_cma_roce_mode = [cma_roce_mode, '-d', mlnx_interface, '-p', '1', '-m', '2']
run_command(set_cma_roce_mode)

set_cma_roce_mode_tos = [cma_roce_tos, '-d', mlnx_interface, '-t', TC]
run_command(set_cma_roce_mode_tos)

enable_ecn = [sysctl, '-w', 'net.ipv4.tcp_ecn=1']
run_command(enable_ecn)

sys_cnp_802p_prio = '/sys/class/net/{}/ecn/roce_np/cnp_802p_prio'.format(interface)
sys_cnp_dscp = '/sys/class/net/{}/ecn/roce_np/cnp_dscp'.format(interface)
sys_np_cnp_prio = '/sys/kernel/debug/mlx5/{}/cc_params/np_cnp_prio'.format(interfaces[interface])
sys_np_cnp_dscp = '/sys/kernel/debug/mlx5/{}/cc_params/np_cnp_dscp'.format(interfaces[interface])

sys_traffic_class = '/sys/class/infiniband/{}/tc/1/traffic_class'.format(mlnx_interface)

if os.path.isfile(sys_traffic_class):
    with open(sys_traffic_class, 'w') as traffic_class:
        traffic_class.write(str(TC))

if os.path.isfile(sys_cnp_802p_prio):
    with open(sys_cnp_802p_prio, 'w') as cnp_802p_prio:
        cnp_802p_prio.write(str(DSCP_CNP_TC))

if os.path.isfile(sys_cnp_dscp):
    with open(sys_cnp_dscp, 'w') as cnp_dscp:
        cnp_dscp.write(str(DSCP_CNP_VALUE))

if os.path.isfile(sys_np_cnp_prio):
    with open(sys_np_cnp_prio, 'w') as np_cnp_prio:
        np_cnp_prio.write(str(DSCP_CNP_TC))

if os.path.isfile(sys_np_cnp_dscp):
    with open(sys_np_cnp_dscp, 'w') as np_cnp_dscp:
        np_cnp_dscp.write(str(DSCP_CNP_VALUE))

interface_auth = [oci_cn_auth, '--interface', interface]
run_command(interface_auth)

# This should be fixed by RHBA-2021:0351, CEBA-2021:0351 and ELBA-2021-0351

# Workaround for timer being stuck on boot on EL7
# restart_timer = [ systemctl, 'restart', 'oci_cn_auth.timer' ]
# run_command(restart_timer)

print('Interface {} configuration complete'.format(interface))
