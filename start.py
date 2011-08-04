#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Starter for the Startuppoker website.

    :copyright: (c) 2011 by it-agile GmbH
    :license: BSD, see LICENSE for more details.
"""

from startuppoker_website import website
from startuppoker_website import couchdb_repository

if __name__ == '__main__':
    website.repository = couchdb_repository
    app = website.start()
    app.debug = True
    app.run()
