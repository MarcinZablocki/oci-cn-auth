import os 
import psutil
import socket
from lib.config import SHAPES

from lib.util import WpaSupplicantService

def get_dev_name_by_id(id): 
    """ This assumes there are no virtual interfaces """
    
    base_path = '/sys/bus/pci/devices/{}/net/'.format(id)
    interface_name=os.listdir(base_path)[0]
    return interface_name

def get_interfaces_by_shape(shape):
    """ get list of interfaces by compute shape """

    interfaces = []

    if shape in SHAPES: 
        ids = SHAPES[shape]
        
        for id in ids: 
            interfaces.append(get_dev_name_by_id(id))

    return interfaces
