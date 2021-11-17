#!/bin/bash
#
# Simple script to read the .version file and put in the service file
# It is called in the Makefile

# Read first line .version - which stores the version of oci-cn-auth
read -r VERSION < .version-oci-cn-auth

# Vomit out the version to oci-cn-auth.service
cat << EOF > src/var/lib/oci-cn-auth/share/oci-cn-auth.service
#
# oci-cn-auth. service providing configuration of wpa_supplicant for specified interface
# to authenticate to OCI cluster network.
#
[Unit]
Description=OCI Cluster Network Authentication: renew WPA certificates (${VERSION})

[Service]
Type=oneshot
ExecStart=/var/lib/oci-cn-auth/oci-cn-auth --start

[Install]
WantedBy=multi-user.target
EOF
