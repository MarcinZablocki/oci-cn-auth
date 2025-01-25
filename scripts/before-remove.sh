rm -f /etc/systemd/system/network.service.d/override.conf
systemctl=$(which systemctl)
${systemctl} stop oci-cn-auth-renew.timer
${systemctl} stop oci-cn-auth.service
${systemctl} disable oci-cn-auth-renew.timer
${systemctl} disable oci-cn-auth.service
${systemctl} reset-failed
