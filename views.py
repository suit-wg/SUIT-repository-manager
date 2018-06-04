import resources

from aiohttp import web
import aiocoap
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


async def coap_send(request):
    data = await request.post()
    target = data['target']
    sign = True if 'signed' in data else False
    digest = data['file']
    fw = None
    logging.info("CoAP send requested with {} to {}".format(digest, target))
    for upload in request.app['uploads']:
        if upload.digest == digest:
            fw = upload
    if not fw:
        raise web.HTTPNotFound
    with fw.path.open('rb') as f:
        content = f.read()

    protocol = await aiocoap.Context.create_client_context()
    request = aiocoap.Message(code=aiocoap.POST, uri=target, payload=content)
    try:
        await protocol.request(request).response
    except Exception as e:
        logging.warning("Error sending coap request: ".format(e))
        return web.Response(text="Error sending file {}"
                                 " to target {}".format(fw.path.name,
                                                        target))
    return web.Response(text="Sent file {} to target {}".format(fw.path.name,
                                                                target))
