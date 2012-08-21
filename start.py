#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Starter for the startuppoker spectator.

    :copyright: (c) 2011 by it-agile GmbH
    :license: BSD, see LICENSE for more details.
"""
import sys
sys.path.append('D:\\development\\')
from startuppoker_spectator import spectator
from startuppoker_spectator import sqlite_repository

debug = False

if __name__ == '__main__':
    try:
        from local_settings import debug
    except ImportError:
        pass
    spectator.repository = sqlite_repository
    app = spectator.app
    app.debug = debug
    app.run()
