"""
test_fileupload.py

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
from unittest.mock import patch

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse
from w3af.core.controllers.ci.php_moth import get_php_moth_http as moth


@pytest.mark.phpmoth
class TestFileUpload(PluginTest):

    file_upload_url = moth('/audit/file_upload/trivial/')

    file_upload_url_534 = (moth('/audit/file_upload/strange_extension_534/'),
                           moth('/audit/file_upload/trivial/'))

    _run_configs = {
        'basic': {
            'target': file_upload_url,
            'plugins': {
                'crawl': (
                    PluginConfig(
                        'web_spider',
                        ('only_forward', True, PluginConfig.BOOL)),
                ),
                'audit': (
                    PluginConfig(
                        'file_upload', ('extensions',
                                        'gif,html,bmp,jpg,png,txt',
                                        PluginConfig.LIST)
                    ),)
            }, },

        'crawling': {
            'target': file_upload_url_534,
            'plugins': {
                'audit': (
                    PluginConfig(
                        'file_upload', ('extensions',
                                        'gif,html,bmp,jpg,png,txt',
                                        PluginConfig.LIST)
                    ),),
                'crawl': (
                    PluginConfig('web_spider',

                                 ('only_forward', True, PluginConfig.BOOL),

                                 ('ignore_regex',
                                  '.*logout.php*',
                                  PluginConfig.STR)),
                )
            }
        },
    }

    def test_reported_file_uploads(self):
        cfg = self._run_configs['basic']
        self._scan(cfg['target'], cfg['plugins'])

        fu_vulns = self.kb.get('file_upload', 'file_upload')
        self.assertEqual(1, len(fu_vulns))

        v = fu_vulns[0]
        self.assertEqual(v.get_name(), 'Insecure file upload')
        self.assertEqual(str(v.get_url().get_domain_path()),
                          self.file_upload_url)

    def test_reported_file_uploads_issue_534(self):
        # https://github.com/andresriancho/w3af/issues/534
        cfg = self._run_configs['crawling']
        self._scan(cfg['target'], cfg['plugins'])

        fu_vulns = self.kb.get('file_upload', 'file_upload')
        self.assertTrue(all(v.get_name() == 'Insecure file upload' for v in fu_vulns))

        EXPECTED_FILES = {'uploader.php', 'uploader.534'}
        found_files = set(v.get_url().get_file_name() for v in fu_vulns)
        self.assertEqual(EXPECTED_FILES, found_files)


@pytest.mark.skip("Works locally, fails in CI - likely because of RNG `with patch()`")
class TestParseOutputFromUpload(PluginTest):

    target_url = 'http://example.org/'

    FORM = """\
          <form enctype="multipart/form-data" action="upload" method="POST">
              <input type="hidden" name="MAX_FILE_SIZE" value="10000000" />
              Choose a file to upload: <input name="uploadedfile" type="file" /><br />
              <input type="submit" value="Upload File" />
          </form>
          """

    RESULT = """Thanks for uploading your file to <a href='/uploads1/foo.png'>x</a>"""

    image_content = 'PNG' + 'B' * 239

    MOCK_RESPONSES = [
              MockResponse(url=target_url,
                           body=FORM,
                           content_type='text/html',
                           method='GET', status=200),

              MockResponse(url=target_url + 'upload',
                           body=RESULT,
                           content_type='text/html',
                           method='POST', status=200),

              MockResponse(url=target_url + 'uploads1/foo.png',
                           body=image_content,
                           content_type='image/png',
                           method='GET', status=200),

    ]

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (PluginConfig('file_upload'),),

                'crawl': (
                    PluginConfig('web_spider',

                                 ('only_forward', True, PluginConfig.BOOL),

                                 ('ignore_regex',
                                  '.*logout.php*',
                                  PluginConfig.STR)),
                )
            },
        }
    }

    def test_parse_response(self):
        cfg = self._run_configs['cfg']

        with patch('w3af.plugins.audit.file_upload.rand_alnum') as rand_alnum_mock:
            rand_alnum_mock.return_value = 'B' * 239

            self._scan(cfg['target'], cfg['plugins'])

        fu_vulns = self.kb.get('file_upload', 'file_upload')
        self.assertEqual(1, len(fu_vulns))

        v = fu_vulns[0]
        self.assertEqual(v.get_name(), 'Insecure file upload')
        self.assertEqual(str(v.get_url().get_domain_path()), self.target_url)


@pytest.mark.skip("Works locally, fails in CI - likely because of rand_alnum `with patch()`")
class TestRegexOutputFromUpload(TestParseOutputFromUpload):

    target_url = 'http://example.org/'

    FORM = """\
          <form enctype="multipart/form-data" action="upload" method="POST">
              <input type="hidden" name="MAX_FILE_SIZE" value="10000000" />
              Choose a file to upload: <input name="uploadedfile" type="file" /><br />
              <input type="submit" value="Upload File" />
          </form>
          """

    RESULT = "Thanks for uploading your file to <pre>../../hackable/uploads/mockname.png</pre>"

    FILE_CONTENT_RAND = 'w3af.core.data.fuzzer.utils.rand_alnum'
    IMAGE_CONTENT = 'PNG' + 'B' * 239

    FILENAME_RAND_ALPHA = 'w3af.core.data.constants.file_templates.file_templates.rand_alpha'

    MOCK_RESPONSES = [
              MockResponse(url=target_url,
                           body=FORM,
                           content_type='text/html',
                           method='GET', status=200),

              MockResponse(url=target_url + 'upload',
                           body=RESULT,
                           content_type='text/html',
                           method='POST', status=200),

              MockResponse(url=target_url + 'hackable/uploads/mockname.png',
                           body=IMAGE_CONTENT,
                           content_type='image/png',
                           method='GET', status=200),
    ]

    def test_parse_response(self):
        with patch(self.FILENAME_RAND_ALPHA) as rand_alpha_mock:
            rand_alpha_mock.return_value = 'mockname'

            with patch('w3af.plugins.audit.file_upload.rand_alnum') as rand_alnum_mock:
                rand_alnum_mock.return_value = 'B' * 239

                cfg = self._run_configs['cfg']
                self._scan(cfg['target'], cfg['plugins'])

        fu_vulns = self.kb.get('file_upload', 'file_upload')
        self.assertEqual(1, len(fu_vulns))

        v = fu_vulns[0]
        self.assertEqual(v.get_name(), 'Insecure file upload')
        self.assertEqual(str(v.get_url().get_domain_path()), self.target_url)
