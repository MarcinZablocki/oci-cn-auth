iter=$1
fpm -s dir \
  -f -n oci-auth \
  -t deb \
  --iteration $iter \
  --category Tools \
  -a noarch \
  -d "python3-psutil" -d "python3-openssl" -d "python3-cryptography" -d "python3-requests" -d "python3-jinja2" -d "wpasupplicant" \
  -d "python" -d "mlnx-ofed-kernel-utils" \
  --description "Oracle Cloud cluster networking authentication utility" \
  --license "UPL-1.0" \
  --vendor "Oracle" \
  --after-install scripts/after-install-deb.sh \
  --after-remove scripts/after-remove.sh \
  --after-upgrade scripts/after-upgrade.sh \
  --before-install scripts/before-install.sh \
  --before-remove scripts/before-remove-deb.sh \
  --before-upgrade scripts/before-upgrade.sh \
  --prefix / \
  --config-files /etc/rdma/oracle_rdma.conf \
  src/var/lib/=/var/lib/ \
  src/bin/oci-auth=/usr/bin/oci-auth \
  src/etc/rdma/oracle_rdma.conf=/etc/rdma/oracle_rdma.conf \
  src/var/lib/oci-auth/share/oci-auth.service=/lib/systemd/system/oci-auth.service \
  src/var/lib/oci-auth/share/oci-auth.timer=/lib/systemd/system/oci-auth.timer \
  src/var/lib/oci-auth/bin/ifup-rdma=/etc/network/if-up.d/ifup-rdma

#  --depends "python36-requests python36-pyOpenSSL python36-jinja2 python36-psutil python36-cryptography" \

