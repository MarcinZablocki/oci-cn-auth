# remove timeout override 
rm -rf /etc/systemd/system/network.service.d/

systemctl=$(which systemctl)
${systemctl} stop oci-cn-auth.timer
${systemctl} stop oci-cn-auth.service
${systemctl} disable oci-cn-auth.timer
${systemctl} disable oci-cn-auth.service
${systemctl} reset-failed

