#!/usr/bin/env python

from aiohttp import web
import aiohttp_jinja2
import jinja2
import aiocoap.resource as resource
import aiocoap

import routes
import resources

import asyncio
import hashlib
import logging
from pathlib import Path
import os.path

PROJECT_ROOT = '.'


def get_files():
    p = Path('./uploads')
    files = []
    for child in p.iterdir():
        with child.open('rb') as f:
            m = hashlib.sha1(f.read()).hexdigest()[:16]
            url = os.path.join('f', m)
            files.append(resources.FirmwareFile(child, url, m))
    return files


@asyncio.coroutine
def init(loop, app):
    srv = yield from loop.create_server(app.make_handler(),
                                        '::1', 8080)
    return srv


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    loop = asyncio.get_event_loop()

    coap = resource.Site()
    coap.add_resource(('.well-known', 'core'),
                      resource.WKCResource(coap.get_resources_as_linkheader))

    app = web.Application(loop=loop)
    aiohttp_jinja2.setup(app,
                         loader=jinja2.FileSystemLoader('templates'))
    app['uploads'] = get_files()
    app['coap'] = coap
    for dpt in app['uploads']:
        resources.add_file_resource(coap, dpt)
    routes.setup_routes(app, PROJECT_ROOT)

    asyncio.Task(aiocoap.Context.create_server_context(coap))
    loop.run_until_complete(init(loop, app))
    print("starting loop!")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
