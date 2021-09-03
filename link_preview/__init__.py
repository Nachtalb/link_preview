from concurrent.futures import ThreadPoolExecutor, as_completed
from http.client import HTTPResponse
from random import choice
import re
from string import Formatter
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .base import BasePlugin
from .html import HTMLParser


USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',  # noqa
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393',  # noqa
]


class InfoParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.data = {}
        self._title_match = False

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == 'meta' and attrs.get('property', '').startswith(('og:', 'twitter:')):
            prop = attrs['property'].split(':', 1)[1]
            if (':' not in prop and
                    prop not in ('image', 'video') and
                    (content := attrs.get('content'))):
                self.data[prop] = content
        if 'title' not in self.data and tag == 'title':
            self._title_match = True

    def handle_data(self, data):
        if self._title_match:
            self.data['title'] = data
            self._title_match = False


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
            'description': '''Domains to ignore
This may come in useful eg. when you have the YouTube Link Preview plugin active that has more
detailed information about youtube videos.

Prefix any regex with r/.

You can use this regex if you use the YouTube plugin (see plugin description to copy it):
"r/(?:www\\.|m\\.)?youtu(?:be\\-nocookie\\.com|\\.be|be\\.com)"
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
        self.parse_ignored()

    def incoming_chat_notification(self, user: str, line: str, room: str = None):
        if (self.frame.np.network_filter.is_user_ignored(user) or
                self.frame.np.network_filter.is_user_ip_ignored(user)):
            return

        urls = self.find_urls(line)
        parser = InfoParser()
        msg_type = self.settings['color'].lower()
        for url, data in self.request_urls(urls):
            parser.reset()
            parser.feed(data)
            if 'url' not in parser.data:
                parser.data['url'] = url

            if msg := self.msg(parser.data):
                if room:
                    self.echo_public(room, msg, msg_type)
                else:
                    self.echo_private(user, msg, msg_type)

    def settings_changed(self, before, after, change):
        if 'ignore' in change['after']:
            self.parse_ignored()

    def parse_ignored(self):
        self.ignored_pure = set(filter(lambda s: not s.startswith('r/'), self.settings['ignore']))  # type: ignore
        self.ignored_reg = []
        errors = []
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
            yield url

    def msg(self, data: dict[str, str]):
        msg = []
        for line in self.settings['template']:
            if any(map(lambda k: '{%s}' % k in line, data.keys())):
                msg.append(self.formatter.format(line, **data).replace('\n', ' '))
        return '\n'.join(msg)

    def incoming_public_chat_notification(self, room: str, user: str, line: str):
        self.incoming_chat_notification(user, line, room)

    def incoming_private_chat_notification(self, user: str, line: str):
        self.incoming_chat_notification(user, line)

    def load_url(self, url: str, timeout: int):
        with urlopen(Request(url=url, headers={'User-Agent': choice(USER_AGENTS)}),
                     timeout=timeout) as conn:
            conn: HTTPResponse
            return conn.read().decode('utf-8')

    def request_urls(self, urls):
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_url = {executor.submit(self.load_url, url, 10): url for url in urls}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    yield url, future.result()
                except Exception as e:
                    self.log(f'Could not load data for {url}: {e}')
