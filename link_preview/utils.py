from functools import wraps
import inspect
from pathlib import Path
from urllib.request import Request, urlopen
import json
from random import choice
from http.client import HTTPResponse
from typing import Union

BASE_PATH = Path(__file__).parent.parent.absolute()

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',  # noqa
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393',  # noqa
]


def command(func):
    @wraps(func)
    def wrapper(self, initiator=None, argstring=None, *_args, **_kwargs):
        if self == initiator:
            initiator = argstring
            argstring, _args = _args[0], _args[1:]
        argspec = inspect.signature(func)
        command_args = list(map(str2num, filter(None, map(str.strip, (argstring or '').split()))))
        extra_args = []

        if 'initiator' in argspec.parameters and 'initiator' not in _kwargs and initiator is not None:  # noqa
            extra_args.append(initiator)
        if 'args' in argspec.parameters and 'args' not in _kwargs and command_args:
            extra_args.append(command_args)

        return func(self, *extra_args, *_args, **_kwargs)
    return wrapper


def str2num(string):
    if string.isdigit():
        return int(string)
    try:
        string = float(string)
    except ValueError:
        pass
    return string


class Response:
    _raw = _content = _json = None
    mime_type = None
    encoding = None

    def __init__(self, obj: HTTPResponse):
        self._wrapped_obj = obj
        self.mime_type = self.headers.get_content_type()
        self.encoding = self.headers.get_content_charset()
        self.content

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        return getattr(self._wrapped_obj, attr)

    def __repr__(self):
        return f'{self.__class__}(url="{self.geturl()}", status={self.status})'

    @property
    def raw(self) -> bytes:
        if not self._raw:
            self._raw = self.read()
        return self._raw

    @property
    def content(self) -> Union[bytes, str]:
        if not self._content:
            try:
                self._content = self.raw.decode(self.encoding or 'utf-8')
            except Exception:
                self._content = self.raw
        return self._content

    @property
    def json(self) -> dict:
        if not self._json:
            self._json = json.loads(self.content)
        return self._json


def get(url, headers={}, data=None, timeout=30):
    if 'User-Agent' not in headers:
        headers['User-Agent'] = choice(USER_AGENTS)

    with urlopen(Request(url=url, data=data, headers=headers), timeout=timeout) as resp:
        return Response(resp)
