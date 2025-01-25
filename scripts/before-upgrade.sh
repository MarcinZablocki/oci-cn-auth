if [ ! -f /etc/systemd/system/network.service.d/override.conf ] ; then
mkdir -p /etc/systemd/system/network.service.d/
cat <<EOF >> /etc/systemd/system/network.service.d/override.conf
[Service]
Type=forking
Restart=no
TimeoutSec=15min
EOF
fi 

systemctl=$(which systemctl)
if [ -e /etc/systemd/system/timers.target.wants/oci-cn-auth.timer ]; then
  ${systemctl} disable oci-cn-auth.timer
fi
${systemctl} daemon-reload 
