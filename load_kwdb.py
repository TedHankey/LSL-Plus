# coding: utf-8

from threading import Thread
import sublime
from ruamel.yaml import YAML


KEYWORD_DATA = None

def load_data():
    sourcePath = 'Packages/{}/kwdb.yaml'.format(__package__)
    global KEYWORD_DATA
    KEYWORD_DATA = YAML().load(sublime.load_resource(sourcePath))
        
def plugin_loaded():
    thread = Thread(target = load_data)
    thread.start()

def plugin_unloaded():
    global KEYWORD_DATA
    KEYWORD_DATA = None