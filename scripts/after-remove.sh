systemctl=$(which systemctl)
${systemctl} daemon-reload
${systemctl} reset-failed
