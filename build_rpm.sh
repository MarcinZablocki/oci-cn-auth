ITERATION=$1
VERSION=0.1.0
PRODUCT_NAME=cn-auth
RPM_NAME=oci-${PRODUCT_NAME}
VENDOR=Oracle
URL="http://oracle.com"
LICENSE="UPL-1.0"
DESCRIPTION="This software provides auto configuration of wpa supplicant for 
Oracle cloud cluster network."

fpm -s dir \
  -f -n oci-auth \
  -t rpm \
  --iteration $ITERATION\
  --category Tools \
  -a noarch \
  --description $DESCRIPTION \
  --license $LICENSE \
  --vendor $VENDOR \
  -d "python36-requests" -d "python36-pyOpenSSL" -d "python36-jinja2" -d "python36-psutil" -d "python36-cryptography" -d "wpa_supplicant" \
  --after-install scripts/after-install.sh \
  --after-remove scripts/after-remove.sh \
  --after-upgrade scripts/after-upgrade.sh \
  --before-install scripts/before-install.sh \
  --before-remove scripts/before-remove.sh \
  --before-upgrade scripts/before-upgrade.sh \
  --prefix / \
  --config-files /etc/rdma/oracle_rdma.conf \
  src/var/lib/=/var/lib/ \
  src/bin/oci-auth=/usr/bin/oci-auth \
  src/etc/rdma/oracle_rdma.conf=/etc/rdma/oracle_rdma.conf \
  src/var/lib/oci-auth/share/oci-auth.service=/lib/systemd/system/oci-auth.service \
  src/var/lib/oci-auth/share/oci-auth.timer=/lib/systemd/system/oci-auth.timer \
  src/var/lib/oci-auth/bin/ifup-rdma=/sbin/ifup-local
