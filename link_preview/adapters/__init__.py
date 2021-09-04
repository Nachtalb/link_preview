from .github import Github
from .default import Default

adapters = [Github, Default]


def matching_adapter(url):
    for adapter in adapters:
        if match := adapter.url_match(url):
            yield adapter(match)
