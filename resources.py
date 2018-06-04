import aiocoap
import aiocoap.resource as resource
from collections import namedtuple
import hashlib
import os.path
from pathlib import Path


def check_exists(uploads, name, digest):
    for upload in uploads:
        if upload.digest == digest:
            return True
        if upload.path.name == name:
            return True
    return False


def add_upload(uploads, coap, name, content):
    m = hashlib.sha1(content).hexdigest()[:16]
    if check_exists(uploads, name, m):
        return None
    with open(os.path.join('./uploads', name), 'wb') as f:
        f.write(content)
    fw = FirmwareFile(Path(os.path.join('uploads', name)),
                      os.path.join('/f', m), m)
    add_file_resource(coap, fw)
    uploads.append(fw)
    return fw


def add_file_resource(coap, fw):
    coap.add_resource(('f', fw.digest),
                      FirmwareResource(fw.path))


class FirmwareFile(namedtuple('FirmwareFile', ['path', 'url', 'digest'])):
        pass


class FirmwareResource(resource.Resource):

    def __init__(self, path):
        super().__init__()
        self.path = path

    async def render_get(self, request):
        content = b""
        with self.path.open('rb') as f:
            content = f.read()
        return aiocoap.Message(payload=content)
