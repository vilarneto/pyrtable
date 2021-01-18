from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional, List

from .base import BaseField


if TYPE_CHECKING:
    from pyrtable._baseandtable import _BaseAndTableProtocol


@dataclass
class _AttachmentThumbnail:
    url: str
    width: int
    height: int

    def download(self) -> bytes:
        import requests

        response = requests.get(self.url)
        return response.content


@dataclass
class _AttachmentThumbnailSet:
    small: Optional[_AttachmentThumbnail] = None
    large: Optional[_AttachmentThumbnail] = None
    full: Optional[_AttachmentThumbnail] = None

    def __post_init__(self):
        if self.small is not None:
            self.small = _AttachmentThumbnail(**self.small)
        if self.large is not None:
            self.large = _AttachmentThumbnail(**self.large)
        if self.full is not None:
            self.full = _AttachmentThumbnail(**self.full)


@dataclass
class Attachment:
    id: str
    url: str
    filename: str
    size: int
    type: str
    width: Optional[int] = None
    height: Optional[int] = None
    thumbnails: Optional[_AttachmentThumbnailSet] = None

    def __post_init__(self):
        if self.thumbnails is not None:
            self.thumbnails = _AttachmentThumbnailSet(**self.thumbnails)

    def download(self) -> bytes:
        import requests

        response = requests.get(self.url)
        return response.content

    def download_to(self, path):
        contents = self.download()
        with open(path, 'wb') as fd:
            fd.write(contents)


class AttachmentField(BaseField):
    def decode_from_airtable(self, value: Optional[List[Dict[str, Any]]], base_and_table: '_BaseAndTableProtocol')\
            -> List[Attachment]:
        if not value:
            return []
        return [Attachment(**item_data) for item_data in value]

    def encode_to_airtable(self, value):
        raise NotImplementedError('AttachmentField is only implemented as a read-only field')

    def __init__(self, *args, **kwargs):
        if not kwargs.get('read_only', False):
            raise AttributeError('AttachmentField is only implemented as a read-only field')
        super().__init__(*args, **kwargs)


__all__ = ['Attachment', 'AttachmentField']
