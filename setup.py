#!/usr/bin/env python3

# This file is part of OpenPlotter.
# Copyright (C) 2022 by Sailoog <https://github.com/openplotter/openplotter-notifications>
#                  
# Openplotter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# any later version.
# Openplotter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Openplotter. If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup
from openplotterNotifications import version

setup (
	name = 'openplotterNotifications',
	version = version.version,
	description = 'OpenPlotter app to manage Signal K notifications.',
	license = 'GPLv3',
	author="Sailoog",
	author_email='info@sailoog.com',
	url='https://github.com/openplotter/openplotter-notifications',
	packages=['openplotterNotifications'],
	classifiers = ['Natural Language :: English',
	'Operating System :: POSIX :: Linux',
	'Programming Language :: Python :: 3'],
	include_package_data=True,
	entry_points={'console_scripts': ['openplotter-notifications=openplotterNotifications.openplotterNotifications:main','openplotter-notifications-visual=openplotterNotifications.visual:main','openplotter-notifications-sound=openplotterNotifications.sound:main','notificationsPostInstall=openplotterNotifications.notificationsPostInstall:main','notificationsPreUninstall=openplotterNotifications.notificationsPreUninstall:main','openplotter-notifications-read=openplotterNotifications.openplotterNotificationsRead:main']},
	data_files=[('share/applications', ['openplotterNotifications/data/openplotter-notifications.desktop']),('share/pixmaps', ['openplotterNotifications/data/openplotter-notifications.png']),],
	)

