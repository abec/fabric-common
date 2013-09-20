#!/usr/bin/env python
from __future__ import with_statement

import inspect
import os
from fabric.api import task, run, sudo, prefix as p
from fabric.contrib.files import exists


config = {
    'path': None,
    'sudo': False,
    'args': "--no-site-packages --clear"
}

def validate_config():
    assert isinstance(config['path'], basestring), "Please provide a config string path for %s" % os.path.basename(inspect.getfile(inspect.currentframe()))
    assert isinstance(config['args'], basestring), "Please provide a config string args for %s" % os.path.basename(inspect.getfile(inspect.currentframe()))

def prefix(path=None):
    validate_config()
    path = path or config['path']
    return p("source %s" % os.path.join(path, "bin", "activate"))

@task
def setup():
    validate_config()
    path = config['path']
    args = config['args']
    exe = config['sudo'] and sudo or run
    if not exists(path):
        exe('mkdir -p %s' % path)
    exe("virtualenv %(path)s %(args)s" % {
        'path': path,
        'args': args
    })
