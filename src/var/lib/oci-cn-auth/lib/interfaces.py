""" Interface helper functions """

import os
import sys

from lib.config import SHAPES


def get_dev_name_by_id(pci_id):
	""" This assumes there are no virtual interfaces
        Returns interface name based on PCI ID
    """

	base_path = f"/sys/bus/pci/devices/{pci_id}/net/"
	interface_name = os.listdir(base_path)[0]
	return interface_name


def get_interfaces_by_shape(shape):
	""" get list of interfaces by compute shape """

	interfaces = []

	if shape in SHAPES:
		ids = SHAPES[shape]

		for pci_id in ids:
			interfaces.append(get_dev_name_by_id(pci_id))
	else:
		sys.exit(f"Unsupported shape. Supported shapes are {SHAPES.keys()} ")
	return interfaces
