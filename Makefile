VERSION=0.1
NAME=oci-auth
CATEGORY=Development
BUILD_ARCH=noarch
OUT=OUT
RELEASE=1
SUMMARY=Oracle Cloud cluster networking authentication utility

LICENSE=UPL-1.0
VENDOR=Oracle
LOCATION=/var/lib/oci-auth/
BUILD_ROOT=build/root
SCRIPTS_ROOT=build/scripts

CONFIGS=$(wildcard etc/*)

FPM_OPTS=-s dir \
	-f -n $(NAME) -v $(VERSION) --iteration $(RELEASE) --category $(CATEGORY) -a $(BUILD_ARCH) \
	--description "$(SUMMARY)" --url $(WEB_URL) --license "$(LICENSE)" --vendor "$(VENDOR)" \
	--depends python36-requests python36-pyOpenSSL python36-jinja2 python36-psutil python36-cryptography\
	--before-install $(SCRIPTS_ROOT)/before-install.sh \
	--after-install $(SCRIPTS_ROOT)/after-install.sh \
	--before-remove $(SCRIPTS_ROOT)/before-remove.sh \
	--after-remove $(SCRIPTS_ROOT)/after-remove.sh \
	--prefix $(LOCATION) --directories $(LOCATION) --config-files /etc \
	--verbose -C $(BUILD_ROOT) .
