systemctl=$(which systemctl)
if [ -e /etc/systemd/system/timers.target.wants/oci-cn-auth.timer ]; then
  rm -f /etc/systemd/system/timers.target.wants/oci-cn-auth.timer
fi
${systemctl} daemon-reload
${systemctl} enable oci-cn-auth.service
echo "Please run systemctl start oci-cn-auth to start RDMA network authentication"
