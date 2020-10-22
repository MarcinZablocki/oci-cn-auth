iter=$1
fpm -s dir \
  -f -n oci-auth \
  -t rpm \
  --iteration $iter\
  --category Tools \
  -a noarch \
  --description "Oracle Cloud cluster networking authentication utility" \
  --license "UPL-1.0" \
  --vendor "Oracle" \
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
  src/etc/rdma/oracle_rdma.conf=/etc/rdma/oracle_rdma.conf \
  src/var/lib/oci-auth/share/oci-auth.service=/lib/systemd/system/oci-auth.service \
  src/var/lib/oci-auth/share/oci-auth.timer=/lib/systemd/system/oci-auth.timer \
  src/usr/bin/oci-auth=/usr/bin/oci-auth
