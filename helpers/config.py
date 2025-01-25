""" Defines the shape and PCI ID mapping of cluster network NIC's """
import json

SHAPES_CONFIG_FILE = "/opt/oci-hpc/oci-cn-auth/configs/shapes.json"


# SHAPES_CONFIG_FILE = "/home/<>/src/oci-cn-auth/configs/shapes.json"


def populate_full_shapes_pci_list():
    """ Function to generate Shapes with PCI Ids"""
    json_data = LoadConfig(SHAPES_CONFIG_FILE)
    dict_shapes_pcis = {}
    for shape_data in json_data["hpc-shapes"]:
        key = shape_data["shape"]
        list_rdma_nics = subkey_list(shape_data["rdma-nics"], "pci")
        dict_shapes_pcis[key] = list_rdma_nics
    return dict_shapes_pcis


def populate_hpc_shapes_list():
    """ Function to populate HPC Shapes"""
    json_data = LoadConfig(SHAPES_CONFIG_FILE)

    hpc_shapes = []
    for shape_data in json_data["hpc-shapes"]:
        if not shape_data["gpu"]:
            hpc_shapes.append(shape_data["shape"])

    return hpc_shapes


def populate_gpu_shapes_list():
    """ Function to populate GPU Shapes"""
    json_data = LoadConfig(SHAPES_CONFIG_FILE)

    hpc_shapes = []
    for shape_data in json_data["hpc-shapes"]:
        if shape_data["gpu"]:
            hpc_shapes.append(shape_data["shape"])

    return hpc_shapes


def LoadConfig(config_filename):
    """ Helper function to load json file"""
    with open(config_filename) as file:
        json_data = json.load(file)
    return json_data


def subkey_list(keys, subkey):
    """ Helper function to get list from json"""
    if keys:
        data = []
        for key in keys:
            data.append(key[subkey])
        return data
    return False


# Dictionary of SHAPES and PCI IDS
SHAPES = populate_full_shapes_pci_list()
HPC_SHAPES = populate_hpc_shapes_list()
GPU_SHAPES = populate_gpu_shapes_list()
