systemctl=$(which systemctl)
${systemctl} daemon-reload
${systemctl} enable --now oci-auth.service
${systemctl} enable --now oci-auth.timer
${systemctl} restart oci-auth.timer