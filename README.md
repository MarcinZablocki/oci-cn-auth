# oci-cn-auth-compute
This tool provides configuration for wpa supplicant services providing 802.1x authentication 
to Oracle Cloud Infrastructure cluster networks. 

# How to build locally

Pre-requisite: install fpm (See https://fpm.readthedocs.io/en/v1.10.0/installing.html)

``make``

# oci-cn-auth geography
utils - contains utilties such as ifup networking scripts 
scripts - Makefile pre/post/after bash scripts
helpers - libraries used by oci-cn-auth utility

# Backwards compatibility with older version of oci-cn-auth

To maintain compatibility with https://github.com/MarcinZablocki/oci-cn-auth and oci-cn-auth-compute-1.x series, the following steps
are taken: 
- after-install_xx script creates the directory format on the target OS (Home for oci-cn-auth-compute v2 is /opt/oci-hpc/oci-cn-auth)
