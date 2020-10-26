chmod a+x /etc/network/if-up.d/ifup-rdma
systemctl=$(which systemctl)
${systemctl} daemon-reload
${systemctl} enable oci-auth.service
${systemctl} enable --now oci-auth.timer
