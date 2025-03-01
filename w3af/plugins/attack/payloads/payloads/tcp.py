import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table
from w3af.core.data.misc.encoding import smart_unicode


class tcp(Payload):
    """
    This payload shows TCP socket information
    """
    def api_read(self):
        result = {}

        def parse_tcp(net_tcp):
            new = []
            line = net_tcp.split('\n')
            items = [i for i in line if i != '']
            for item in items:
                tmp = item.split(' ')
                tmp = [i for i in tmp if i != '']
                new.append(tmp)
            new = [i for i in new if i != '']
            return new

        def get_username(etc_passwd, user):
            user = re.search(
                r'(\w*):(\w*):\d*:' + user, etc_passwd, re.MULTILINE)
            if user:
                return user.group(1)
            else:
                return ''

        def split_ip(ip):
            ipPort = [ip[:8], ip[9:]]
            return ipPort

        def dec_to_dotted_quad(n):
            d = 256 * 256 * 256
            q = []
            while d > 0:
                m, n = divmod(n, d)
                q.append(str(m))
                d = int(d / 256)
            q.reverse()
            return '.'.join(q)

        etc = smart_unicode(self.shell.read('/etc/passwd'))
        #TODO: Read UDP and TCP6?
        parsed_info = parse_tcp(smart_unicode(self.shell.read('/proc/net/tcp')))

        for parsed_line in parsed_info:
            try:
                if parsed_line[1] != 'local_address':
                    ip = split_ip(parsed_line[1])
                    parsed_line[1] = str(dec_to_dotted_quad(
                        int(ip[0], 16))) + ':' + str(int(ip[1], 16))

                if parsed_line[2] != 'rem_address':
                    ip = split_ip(parsed_line[2])
                    parsed_line[2] = str(dec_to_dotted_quad(
                        int(ip[0], 16))) + ':' + str(int(ip[1], 16))

                if parsed_line[7] == 'tm->when':
                    parsed_line[7] = 'uid'

                if parsed_line[7] != 'uid':
                    parsed_line[7] = get_username(etc, parsed_line[7])

                if parsed_line[0] != 'sl':
                    key = str(parsed_line[0].replace(':', ''))
                    result[key] = {'local_address': parsed_line[1], 'rem_address': parsed_line[2],
                                   'st': parsed_line[3], 'uid': parsed_line[7], 'inode': parsed_line[11]}
            except:
                pass

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            return 'No TCP information was identified.'
        else:
            rows = []
            rows.append(['Id', 'Local Address',
                        'Remote Address', 'Status', 'User', 'Inode'])
            rows.append([])

            for key in api_result:
                local_address = api_result[key]['local_address']
                rem_address = api_result[key]['rem_address']
                st = api_result[key]['st']
                uid = api_result[key]['uid']
                inode = api_result[key]['inode']

                rows.append([key, local_address, rem_address, st, uid, inode])

            result_table = table(rows)
            result_table.draw(80)
            return rows
