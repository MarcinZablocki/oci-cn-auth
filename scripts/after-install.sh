chmod a+x /sbin/ifup-local
systemctl=$(which systemctl)
${systemctl} daemon-reload
${systemctl} enable oci-cn-auth.service
${systemctl} enable --now oci-cn-auth.timer
