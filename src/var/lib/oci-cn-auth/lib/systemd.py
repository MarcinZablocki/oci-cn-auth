#!/usr/bin/env python3
import shutil
import lib.util


def _systemctl_run(command, service):
	systemctl = shutil.which('systemctl')
	command = [systemctl, command, service]
	return lib.util.run_command(command)


def is_active(service):
	""" Checks if service is active """
	return _systemctl_run('is-active', service)


def is_enabled(service):
	""" Checks if service is enabled """

	return _systemctl_run('is-enabled', service)


def enable(service):
	""" enable systemd unit """
	return _systemctl_run('enable', service)


def disable(service):
	""" disable systemd unit """
	return _systemctl_run('disable', service)


def start(service):
	""" start systemd unit """
	return _systemctl_run('start', service)


def stop(service):
	""" stop systemd unit """
	return _systemctl_run('stop', service)


def reload():
	systemctl = shutil.which('systemctl')
	return lib.util.run_command([systemctl, 'daemon-reload'])
