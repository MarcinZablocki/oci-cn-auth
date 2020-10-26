import os 

SHAPES = { 
    'BM.GPU4.8' : ["0000:48:00.0", "0000:4c:00.0", "0000:0c:00.0", "0000:16:00.0", "0000:c3:00.0", "0000:d1:00.0", "0000:8a:00.0", "0000:94:00.0"],
    'BM.HPC2.36' : ["0000:5e:00.0"]       
}

def get_dev_name_by_id(id): 
    """ This assumes there are no virtual interfaces """
    base_path = '/sys/bus/pci/devices/{}/net/'.format(id)
    interface_name=os.listdir(base_path)[0]
    return interface_name

def get_interfaces_by_shape(shape):
    interfaces = []
    ids = SHAPES[shape]
    
    for id in ids: 
        interfaces.append(get_dev_name_by_id(id))

    return interfaces
