from ..utils import get
from ..html import HTMLParser


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


class Default:
    @staticmethod
    def url_match(url):
        return url

    def __init__(self, url):
        self.url = url
        self.parser = InfoParser()

    def get_data(self):
        try:
            response = get(self.url, timeout=15)
        except Exception:
            return

        if not isinstance(response.content, str) or not response.mime_type or not response.mime_type.startswith('text/'):  # noqa
            return

        self.parser.feed(response.content)
        if 'url' not in self.parser.data:
            self.parser.data['url'] = self.url

        return self.parser.data
