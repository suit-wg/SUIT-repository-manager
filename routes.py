import views

import os.path


def setup_routes(app, root):
    app.router.add_get('/', views.index)
    app.router.add_get('/files', views.files)
    app.router.add_post('/files', views.file_upload)
    app.router.add_get('/f/{digest}', views.file_by_digest)
    app.router.add_static('/f', path=os.path.join(root, 'uploads'), name='f')
