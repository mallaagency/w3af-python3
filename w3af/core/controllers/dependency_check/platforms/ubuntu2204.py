"""
ubuntu2204.py

Copyright 2018 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import distro

from .ubuntu1604 import Ubuntu1604


class Ubuntu2204(Ubuntu1604):
    SYSTEM_NAME = 'Ubuntu 22.04'

    def __init__(self):
        super(Ubuntu2204, self).__init__()

    @staticmethod
    def is_current_platform():
        return 'Ubuntu' in distro.name() and '22.04' in distro.version()

