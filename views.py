import resources

from aiohttp import web
import aiohttp_jinja2
from multidict import MultiDict

import logging


async def index(request):
    return web.Response(text='Hello world!')


@aiohttp_jinja2.template('files.jinja2')
async def files(request):
    return {'files': request.app['uploads']}


async def file_upload(request):
    data = await request.post()
    fw_data = data['firmware']
    fw_file = fw_data.file
    logging.debug("upload on file {}".format(fw_data.filename))
    content = fw_file.read()
    fw = resources.add_upload(request.app['uploads'],
                              request.app['coap'],
                              fw_data.filename, content)
    if not fw:
        raise web.HTTPUnprocessableEntity
    return web.Response(text='{} with digest {} stored'.format(fw.path.name,
                                                               fw.digest))


async def file_by_digest(request):
    digest = request.match_info['digest']
    uploads = request.app['uploads']
    req_fw = None
    for fw in uploads:
        if fw.digest == digest:
            req_fw = fw
    if not req_fw:
        raise web.HTTPNotFound
    with req_fw.path.open('rb') as f:
        data = f.read()
    hdrs = MultiDict({'Content-Disposition':
                      'Attachment;filename={}'.format(req_fw.path.name)})
    return web.Response(headers=hdrs,
                        body=data)
