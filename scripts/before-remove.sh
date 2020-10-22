systemctl=$(which systemctl)
${systemctl} stop oci-auth.timer
${systemctl} stop oci-auth.service
${systemctl} disable oci-auth.timer
${systemctl} disable oci-auth.service
${systemctl} reset-failed