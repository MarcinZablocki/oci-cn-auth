# build oci_cn_auth

PKG_NAME=oci-cn-auth
PKG_DESCRIPTION="OCI cluster network authentication tool"
PKG_VERSION=2.0.25
PKG_RELEASE=compute
PKG_MAINTAINER="OCI Compute <compute_dev_us_grp@oracle.com>"
PKG_ARCH=all
PKG_ARCH_RPM=noarch
PKG_LICENSE="UPL-1.0"
PKG_VENDOR=Oracle

PKG_DEB=${PKG_NAME}_${PKG_VERSION}-${PKG_RELEASE}_${PKG_ARCH}.deb
EL7_RPM=${PKG_NAME}-${PKG_VERSION}-${PKG_RELEASE}.el7.${PKG_ARCH_RPM}.rpm
EL8_RPM=${PKG_NAME}-${PKG_VERSION}-${PKG_RELEASE}.el8.${PKG_ARCH_RPM}.rpm
SLES_RPM=${PKG_NAME}-${PKG_VERSION}-${PKG_RELEASE}.sles.${PKG_ARCH_RPM}.rpm

TGT_DIR=/opt/oci-hpc/oci-cn-auth
REL_TGT_DIR=$(shell echo ${TGT_DIR} | cut -c2-)

FPM_OPTS=-s dir -f -n oci-cn-auth \
	-v $(PKG_VERSION) \
	--iteration $(PKG_RELEASE) \
	--maintainer ${PKG_MAINTAINER} \
	--description $(PKG_DESCRIPTION) \
	-a $(PKG_ARCH) \
	--license ${PKG_LICENSE} \
	--vendor ${PKG_VENDOR} \
	--rpm-os linux \
	--exclude $(REL_TGT_DIR)/services/*.in

EL7_DEPS=-d "python36-requests" -d "python36-pyOpenSSL" -d "python36-jinja2" -d "python36-psutil" -d "python36-cryptography" -d "wpa_supplicant"
EL8_DEPS=-d "python3-requests" -d "python3-pyOpenSSL" -d "python3-jinja2" -d "python3-psutil" -d "python3-cryptography" -d "wpa_supplicant"
SLES_DEPS=-d "python3-requests" -d "python3-pyOpenSSL" -d "python3-Jinja2" -d "python3-psutil" -d "python3-cryptography" -d "wpa_supplicant"
DEB_DEPS=-d "python3-psutil" -d "python3-openssl" -d "python3-cryptography" -d "python3-requests" -d "python3-jinja2" -d "wpasupplicant" -d "mlnx-ofed-kernel-utils" -d "ifupdown"

FILES=oci_cn_auth=${TGT_DIR}/oci_cn_auth \
	__init__.py=${TGT_DIR}/__init__.py \
	helpers=$(TGT_DIR) \
	configs=${TGT_DIR} \
	services=${TGT_DIR} \
        usr \
	configs/oracle_rdma.conf=/etc/rdma/oracle_rdma.conf \
	services/oci-cn-auth.service=/lib/systemd/system/oci-cn-auth.service \
	services/oci-cn-auth-renew.service=/lib/systemd/system/oci-cn-auth-renew.service \
	services/oci-cn-auth-renew.timer=/lib/systemd/system/oci-cn-auth-renew.timer \
	.version-oci_cn_auth=$(TGT_DIR)/.version-oci_cn_auth

DEB_FILES=utils/ifup_rdma.py=/sbin/ifup-rdma \
  utils/ifup-local=/etc/network/if-up.d/ifup-rdma
RPM_FILES=utils/ifup_rdma.py=/sbin/ifup-rdma \
  utils/ifup-local=/sbin/ifup-local

HPC_SHAPES_URL="https://hpc.objectstorage.eu-frankfurt-1.oci.customer-oci.com/p/5_q6-lZlI1kFGRhdFvhiJ2aE9QPqdyigomBtq3QMBogZz1A4kyHbdnVaKh0bLOsu/n/hpc/b/hpc-shape-config/o/shapes.json"

RPM_SCRIPTS=--after-install scripts/after-install.sh \
  --after-remove scripts/after-remove.sh \
  --after-upgrade scripts/after-upgrade.sh \
  --before-install scripts/before-install.sh \
  --before-remove scripts/before-remove.sh \
  --before-upgrade scripts/before-upgrade.sh

DEB_SCRIPTS=--after-install scripts/after-install-deb.sh \
  --after-remove scripts/after-remove.sh \
  --after-upgrade scripts/after-upgrade-deb.sh \
  --before-install scripts/before-install.sh \
  --before-remove scripts/before-remove-deb.sh \
  --before-upgrade scripts/before-upgrade.sh

.PHONY: all prod clean generate_versioned_files generate_symbolic_link upload_artifacts_to_hpc_tenancy upload_to_osi_artifactory download_shapes_config

all: clean download_shapes_config generate_versioned_files generate_symbolic_link $(EL7_RPM) $(EL8_RPM) $(PKG_DEB) $(SLES_RPM)
prod: clean download_shapes_config generate_versioned_files generate_symbolic_link $(EL7_RPM) $(EL8_RPM) $(PKG_DEB) $(SLES_RPM) upload_artifacts_to_hpc_tenancy


$(SLES_RPM):
	fpm --verbose -t rpm -p ${SLES_RPM} ${FPM_OPTS} ${SLES_DEPS} ${RPM_SCRIPTS} ${FILES} ${RPM_FILES}

$(EL7_RPM):
	fpm --verbose -t rpm -p ${EL7_RPM} ${FPM_OPTS} ${EL7_DEPS} ${RPM_SCRIPTS} ${FILES} ${RPM_FILES}

$(EL8_RPM):
	fpm --verbose -t rpm -p ${EL8_RPM} ${FPM_OPTS} ${EL8_DEPS} ${RPM_SCRIPTS} ${FILES} ${RPM_FILES}

$(PKG_DEB):
	fpm --verbose --deb-no-default-config-files -t deb -p ${PKG_DEB} ${FPM_OPTS} ${DEB_DEPS} ${DEB_SCRIPTS} ${FILES} ${DEB_FILES}

clean:
	rm -f *.deb *.rpm services/oci-cn-auth.service services/oci-cn-auth-renew.service services/oci-cn-auth-renew.timer .version-oci_cn_auth

.version-oci_cn_auth:
	echo ${PKG_VERSION}-${PKG_RELEASE} > .version-oci_cn_auth

oci-cn-auth.service oci-cn-auth-renew.service oci-cn-auth-renew.timer:
	sed 's/__VERSION__/${PKG_VERSION}-${PKG_RELEASE}/g' services/$@.in > services/$@

generate_versioned_files: oci-cn-auth.service oci-cn-auth-renew.service oci-cn-auth-renew.timer .version-oci_cn_auth

generate_symbolic_link:
	mkdir -p usr/bin
	ln -sf /opt/oci-hpc/oci-cn-auth/oci_cn_auth usr/bin/oci-cn-auth

download_shapes_config:
	curl -X GET ${HPC_SHAPES_URL} -o configs/shapes.json
