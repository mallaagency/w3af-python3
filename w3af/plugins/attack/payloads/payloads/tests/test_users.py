"""
test_users.py

Copyright 2012 Andres Riancho

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
import pytest

from w3af.plugins.attack.payloads.payloads.tests.apache_payload_test_helper import ApachePayloadTestHelper
from w3af.plugins.attack.payloads.payload_handler import exec_payload


@pytest.mark.w3af_moth
class TestUsers(ApachePayloadTestHelper):
    EXPECTED_RESULT = {'root', 'bin', 'daemon', 'uucp', 'www-data',
                       'sshd', 'nobody', 'list', 'sync', 'sys',
                       'moth', 'games', 'proxy', 'lp', 'news',
                       'mail', 'gnats', 'irc', 'backup', 'mysql',
                       'man', '_apt', 'postfix'}

    def test_users(self):
        result = exec_payload(self.shell, 'users', use_api=True)
        self.assertEqual(self.EXPECTED_RESULT, set(result.keys()))
