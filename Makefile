# build oci-cn-auth 

PKG_NAME=oci-cn-auth
PKG_DESCRIPTION="OCI cluster network authentication tool" 
PKG_VERSION=0.2.3
PKG_RELEASE=1
PKG_MAINTAINER="Marcin Zablocki \<marcin.zablocki@oracle.com\>"
PKG_ARCH=all
PKG_ARCH_RPM=noarch
PKG_LICENSE="UPL-1.0"
PKG_VENDOR=Oracle

PKG_DEB=${PKG_NAME}_${PKG_VERSION}-${PKG_RELEASE}_${PKG_ARCH}.deb
EL7_RPM=${PKG_NAME}-${PKG_VERSION}-${PKG_RELEASE}.el7.${PKG_ARCH_RPM}.rpm
EL8_RPM=${PKG_NAME}-${PKG_VERSION}-${PKG_RELEASE}.el7.${PKG_ARCH_RPM}.rpm

FPM_OPTS=-s -f -n oci-cn-auth \
	-v $(PKG_VERSION) \
	--iteration $(PKG_RELEASE) \
	-C $(TMPINSTALLDIR) \
	--maintainer ${PKG_MAINTAINER} \
	--description $(PKG_DESCRIPTION) \
	-a $(PKG_ARCH) \
	--license ${PKG_LICENSE} \
	--vendor ${PKG_VENDOR}

EL7_DEPS=-d "python36-requests" -d "python36-pyOpenSSL" -d "python36-jinja2" -d "python36-psutil" -d "python36-cryptography" -d "wpa_supplicant" 
EL8_DEPS=-d "python3-requests" -d "python3-pyOpenSSL" -d "python3-jinja2" -d "python3-psutil" -d "python3-cryptography" -d "wpa_supplicant" 
DEB_DEPS=-d "python3-psutil" -d "python3-openssl" -d "python3-cryptography" -d "python3-requests" -d "python3-jinja2" -d "wpasupplicant" -d "python" -d "mlnx-ofed-kernel-utils"

FILES=--prefix / \
  --config-files /etc/rdma/oracle_rdma.conf \
  src/var/lib/=/var/lib/ \
  src/bin/oci-cn-auth=/usr/bin/oci-cn-auth \
  src/etc/rdma/oracle_rdma.conf=/etc/rdma/oracle_rdma.conf \
  src/var/lib/oci-cn-auth/share/oci-cn-auth.service=/lib/systemd/system/oci-cn-auth.service \
  src/var/lib/oci-cn-auth/share/oci-cn-auth.timer=/lib/systemd/system/oci-cn-auth.timer

DEB_FILES=src/var/lib/oci-cn-auth/bin/ifup-rdma=/etc/network/if-up.d/ifup-rdma
RPM_FILES=src/var/lib/oci-cn-auth/bin/ifup-rdma=/sbin/ifup-local

RPM_SCRIPTS=--after-install scripts/after-install.sh \
  --after-remove scripts/after-remove.sh \
  --after-upgrade scripts/after-upgrade.sh \
  --before-install scripts/before-install.sh \
  --before-remove scripts/before-remove.sh \
  --before-upgrade scripts/before-upgrade.sh

DEB_SCRIPTS=--after-install scripts/after-install-deb.sh \
  --after-remove scripts/after-remove.sh \
  --after-upgrade scripts/after-upgrade.sh \
  --before-install scripts/before-install.sh \
  --before-remove scripts/before-remove-deb.sh \
  --before-upgrade scripts/before-upgrade.sh 

TMPINSTALLDIR=/tmp/$(PKG_NAME)-fpm-install


el7: ${EL7_RPM}
    
	fpm -t rpm -p ${PKG_RPM} ${FPM_OPTS} \
	  ${EL7_DEPS} \
	  ${RPM_SCRIPTS} \
	  ${FILES} \
	  ${RPM_FILES}

el8: ${EL8_RPM}
	fpm -t rpm -p ${PKG_RPM} ${FPM_OPTS} \
	  ${EL8_DEPS} \
	  ${FILES} \
	  ${RPM_FILES}

.PHONY: deb
deb: ${PKG_DEB}
	fpm -t deb -p ${PKG_DEB} ${FPM_OPTS} \
	  ${DEB_DEPS} \
	  ${DEB_SCRIPTS} \
	  ${FILES} \
	  ${DEB_FILES}
