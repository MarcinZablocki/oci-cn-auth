# oci-cn-auth

This tool provides configuration for wpa supplicant services providing 802.1x authentication 
to Oracle Cloud Infrastructure cluster networks. 

Currently supported operating systems are: 
* Oracle Linux 7
* Oracle Linux 8
* Centos 7
* Centos 8
* Debian 9 (Stretch) 
* Debian 10 (Buster) 
* Ubuntu 16.04 (Xenial) 
* Ubuntu 18.04 (Bionic) 
* Ubuntu 20.04 (Focal) 
* SLES15 SP3

# Configuration 

Configuration file is located in: /etc/rdma/oracle_rdma.conf

In typical scenarios no configuration is required for application to work. 

##  Disable IP requirement
By default only interfaces with IP addresses configured are enabled. To change that behavior use: 

`require_ip=False`

## Manual interface configuration
By default application will detect interface names based on PCI ID map corresponding to shape. 
Interface names can be set manually using

`interfaces=eth0,eth1,eth2`
