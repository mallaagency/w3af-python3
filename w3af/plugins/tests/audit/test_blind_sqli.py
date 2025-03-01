"""
test_blind_sqli.py

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

from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.controllers.ci.w3af_moth import get_w3af_moth_http
from w3af.core.controllers.ci.wavsep import get_wavsep_http


CONFIG = {'audit': (PluginConfig('blind_sqli'),),
          'crawl': (PluginConfig('web_spider',
                    ('only_forward', True, PluginConfig.BOOL)),)}


@pytest.mark.moth
class TestDjangoBlindSQLI(PluginTest):

    def test_integer(self):
        target_url = get_moth_http('/audit/blind_sqli/where_integer_qs.py')
        qs = '?id=1'
        self._scan(target_url + qs, CONFIG)

        vulns = self.kb.get('blind_sqli', 'blind_sqli')
        self.assertEqual(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEqual('Blind SQL injection vulnerability', vuln.get_name())
        self.assertFalse('time delays' in vuln.get_desc())
        self.assertEqual("numeric", vuln['type'])
        self.assertEqual(target_url, str(vuln.get_url()))

    def test_single_quote(self):
        target_url = get_moth_http('/audit/blind_sqli/where_string_single_qs.py')
        qs = '?uname=pablo'
        self._scan_single_quote(target_url, qs)

    def test_single_quote_non_true_value_as_init(self):
        target_url = get_moth_http('/audit/blind_sqli/where_string_single_qs.py')
        qs = '?uname=foobar39'
        self._scan_single_quote(target_url, qs)

    def _scan_single_quote(self, target_url, qs):
        self._scan(target_url + qs, CONFIG)

        vulns = self.kb.get('blind_sqli', 'blind_sqli')
        self.assertEqual(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEqual('Blind SQL injection vulnerability', vuln.get_name())
        self.assertFalse('time delays' in vuln.get_desc())
        self.assertEqual('string_single', vuln['type'])
        self.assertEqual(target_url, str(vuln.get_url()))

    def test_found_exploit_blind_sqli_form(self):
        # Run the scan
        target = get_moth_http('/audit/blind_sqli/blind_where_integer_form.py')
        self._scan(target, CONFIG)

        # Assert the general results
        vulns = self.kb.get('blind_sqli', 'blind_sqli')

        self.assertEqual(1, len(vulns))
        vuln = vulns[0]

        self.assertEqual('Blind SQL injection vulnerability', vuln.get_name())
        self.assertEqual('text', vuln.get_mutant().get_token_name())
        self.assertEqual('blind_where_integer_form.py',
                          vuln.get_url().get_file_name())

    def test_found_exploit_blind_sqli_form_GET(self):
        # Run the scan
        target = get_moth_http('/audit/blind_sqli/blind_where_integer_form_get.py')
        self._scan(target, CONFIG)

        # Assert the general results
        vulns = self.kb.get('blind_sqli', 'blind_sqli')

        self.assertEqual(1, len(vulns))
        vuln = vulns[0]

        self.assertEqual('Blind SQL injection vulnerability', vuln.get_name())
        self.assertEqual('q', vuln.get_mutant().get_token_name())
        self.assertEqual('blind_where_integer_form_get.py',
                          vuln.get_url().get_file_name())


@pytest.mark.wavsep
class TestReflectedXSSFalsePositive(PluginTest):

    def test_xss_false_positive_1516(self):
        target_url = get_wavsep_http('/wavsep/active/Reflected-XSS/'
                                     'RXSS-Detection-Evaluation-GET/'
                                     'Case24-Js2ScriptTag.jsp?userinput=1234')
        self._scan(target_url, CONFIG)

        vulns = self.kb.get('blind_sqli', 'blind_sqli')
        self.assertEqual(0, len(vulns))


@pytest.mark.w3af_moth
class TestOldMothBlindSQLI(PluginTest):

    base_path = '/w3af/audit/blind_sql_injection/'
    target_url = get_w3af_moth_http(base_path)

    config = {
        'audit': (PluginConfig('blind_sqli'),),

        'crawl': (PluginConfig('web_spider',
                               ('only_forward', True, PluginConfig.BOOL),
                               ('ignore_regex', '.*(asp|aspx)', PluginConfig.STR)),),
    }

    def test_found_blind_sqli_old_moth(self):
        expected_path_param = {
            ('bsqli_string.php', 'email'),
            ('bsqli_integer.php', 'id'),
            ('forms/data_receptor.php', 'user'),
            ('completely_bsqli_single.php', 'email'),
            ('bsqli_string_rnd.php', 'email'),
            ('completely_bsqli_double.php', 'email'),
            ('completely_bsqli_integer.php', 'id'),
        }

        ok_to_miss = {
            # Just the HTML to have a form
            'forms/',
            'forms/test_forms.html',

            # False positive tests, these must NOT be detected by blind_sqli
            'random_500_lines.php',
            'random_500_lines_static.php',
            'random_50_lines.php',
            'random_50_lines_static.php',
            'random_5_lines.php',
            'random_5_lines_static.php',
            'delay_random.php',
        }
        skip_startwith = set()
        kb_addresses = {('blind_sqli', 'blind_sqli')}

        self._scan_assert(self.config,
                          expected_path_param,
                          ok_to_miss,
                          kb_addresses,
                          skip_startwith)
