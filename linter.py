# coding: utf-8

import sublime
from SublimeLinter.lint import Linter, util


class Lslint(Linter):

    cmd = ('lslint', '${args}', '${temp_file}')
    defaults = {
        'selector': 'source.lsl',
        'args': ['-i']
    }
    error_stream = util.STREAM_STDERR
    multiline = True
    regex = r'''(?x)
        (?:
            (?:(?P<warning>(?:.)?WARN)|(?P<error>ERROR))
            \:\:\s\(\s*
            (?P<line>[0-9]+)
            \,\s*
            (?P<col>[0-9]+)
            \)\:\s
            (?P<message>.*)
        )
    '''
    tempfile_suffix = 'lsl'

    # The word_re argument is a regex that determines the highlighting of a problem.
    # Defaults to '^([-\w]+)', i.e. highlight the word.
    word_re = None