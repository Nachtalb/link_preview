from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from string import Formatter
from urllib.parse import urlparse
from .adapters import matching_adapter

from .base import BasePlugin


class MessageFormatter(Formatter):
    def get_value(self, key, args, kwargs):
        try:
            return super().get_value(key, args, kwargs)
        except KeyError:
            return ''


class Plugin(BasePlugin):
    settings = {
        'color': 'Action',
        'template': ['* Title: {site_name} {title}', '* Description: {description}'],
        'ignore': [],
        'whitelist': [],
    }
    metasettings = {
        'color': {
            'description': 'Message Colour',
            'type': 'dropdown',
            'options': ('Remote', 'Local', 'Action', 'Hilite'),
        },
        'template': {
            'description': '''Link Preview
Available placeholders: {title}, {description}, {site_name}, {url}
''',
            'type': 'list string'
        },
        'ignore': {
            'description': '''Domain Blacklist
This may come in useful eg. when you have the YouTube Link Preview plugin active that has more
detailed information about youtube videos.

Prefix any regex with r/.

You can use this regex if you use the YouTube plugin (see plugin description to copy it):
"r/(?:www\\.|m\\.)?youtu(?:be\\-nocookie\\.com|\\.be|be\\.com)"
''',  # noqa
            'type': 'list string'
        },
        'whitelist': {
            'description': '''Domain Whitelist
Works the same as the blacklist but the other way around. Blacklist will be ignored.
''',  # noqa
            'type': 'list string'
        },
    }
    url_reg = re.compile(r'https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,4}\b(?:[-a-zA-Z0-9@:%_\+.~#?&//=]*)')  # noqa
    title_temp = '* Title: {title}'
    desc_temp = '* Description: {description}'
    formatter = MessageFormatter()

    def init(self):
        super().init()
        self.ignored_pure = self.ignored_reg = []
        self.whitelist_pure = self.whitelist_reg = []
        self.parse_ignored()

    def incoming_chat_notification(self, user: str, line: str, room: str = None):
        if (self.frame.np.network_filter.is_user_ignored(user) or
                self.frame.np.network_filter.is_user_ip_ignored(user)):
            return

        urls = self.find_urls(line)
        msg_type = self.settings['color'].lower()
        for data in self.request_urls(urls):
            if msg := self.msg(data):
                if room:
                    self.echo_public(room, msg, msg_type)
                else:
                    self.echo_private(user, msg, msg_type)

    def settings_changed(self, before, after, change):
        if 'ignore' in change['after'] or 'whitelist' in change['after']:
            self.parse_ignored()

    def parse_ignored(self):
        self.ignored_pure = set(filter(lambda s: not s.startswith('r/'), self.settings['ignore']))  # type: ignore
        self.ignored_reg = []

        self.whitelist_pure = set(filter(lambda s: not s.startswith('r/'), self.settings['whitelist']))  # type: ignore
        self.whitelist_reg = []

        errors = []
        for reg in set(self.settings['whitelist']) - self.whitelist_pure:
            reg = reg[2:]
            try:
                self.whitelist_reg.append(re.compile(reg))
            except re.error as e:
                errors.append(f'"{reg}": {e}')

        if not self.whitelist_pure and not self.whitelist_reg:
            for reg in set(self.settings['ignore']) - self.ignored_pure:
                reg = reg[2:]
                try:
                    self.ignored_reg.append(re.compile(reg))
                except re.error as e:
                    errors.append(f'"{reg}": {e}')

        if errors:
            error_msg = 'Could not parse the following regex patterns:\n- ' + '\n- '.join(errors)
            self.error_window(error_msg)

    def find_urls(self, string):
        urls = self.url_reg.findall(string)
        for url in urls:
            parsed = urlparse(url)
            if (not parsed.netloc or
                    parsed.netloc in self.ignored_pure or
                    any(map(lambda r: re.match(r, parsed.netloc), self.ignored_reg))):
                continue

            if ((self.whitelist_reg or self.whitelist_pure) and
                    parsed.netloc not in self.whitelist_pure and
                    not any(map(lambda r: re.match(r, parsed.netloc), self.whitelist_reg))):
                continue
            yield url

    def msg(self, data: dict[str, str]):
        msg = []

        if 'site_name' in data and 'title' in data and data['title'].startswith(data['site_name']):
            # Often titles already include the sitename at the start
            data['site_name'] = ''

        for line in self.settings['template']:
            if any(map(lambda k: '{%s}' % k in line, data.keys())):
                msg.append(self.formatter.format(line, **data).replace('\n', ' '))
        return '\n'.join(msg)

    def incoming_public_chat_notification(self, room: str, user: str, line: str):
        self.incoming_chat_notification(user, line, room)

    def incoming_private_chat_notification(self, user: str, line: str):
        self.incoming_chat_notification(user, line)

    def get_url_info(self, url):
        for gatherer in matching_adapter(url):
            if data := gatherer.get_data():
                return data

    def request_urls(self, urls):
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_url = {executor.submit(self.get_url_info, url): url for url in urls}
            for future in as_completed(future_to_url):
                try:
                    content = future.result()
                    if content:
                        yield content
                except Exception as e:
                    self.log(f'Could not load data for {future_to_url[future]}: {e}')
