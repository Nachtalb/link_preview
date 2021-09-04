import re
from ..utils import get
from .default import Default
from urllib.parse import urlparse


class Github:
    pattern = re.compile(r'\/github\.com\/([^/]+\/[^/]+)\/?$')

    @staticmethod
    def url_match(url):
        if urlparse(url).netloc == 'github.com':
            return url

    def __init__(self, url):
        self.repo = None
        self.url = url

        if match := self.pattern.search(url):
            self.repo = match.groups()[0]

    def api_data(self):
        try:
            info = get(f'https://api.github.com/repos/{self.repo}').json
        except Exception:
            return

        info.update({
            'title': info['full_name'],
            'site_name': 'GitHub',
            'url': info['html_url']
        })
        return info

    def get_data(self):
        info = None
        if self.repo and (info := self.api_data()):
            return info

        default_parser = Default(self.url)
        if info := default_parser.get_data():
            # Github annoyingli appends the description with the title .....
            info['description'] = info['description'].replace(info['title'], '').strip(' -')

        return info
