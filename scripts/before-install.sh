# increase network service timeout to 15 minutes
mkdir -p /etc/systemd/system/network.service.d/
cat <<EOF >> /etc/systemd/system/network.service.d/override.conf
[Service]
Type=forking
Restart=no
TimeoutSec=15min
EOF