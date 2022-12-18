# coding: utf-8

import sublime

KEYWORD_DATA = None

def load_data():
    path = 'Packages/{}/kwdb.json'.format(__package__)
    data_file = sublime.load_resource(path)
    global KEYWORD_DATA
    KEYWORD_DATA = sublime.decode_value(data_file)

def plugin_loaded():
    sublime.set_timeout_async(load_data, 100)

def plugin_unloaded():
    global KEYWORD_DATA
    KEYWORD_DATA = None
