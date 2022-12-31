# coding: utf-8

import sublime
import sublime_plugin

SL_WIKI_URL = 'https://wiki.secondlife.com/wiki/'


class LSLTooltips(sublime_plugin.EventListener):
   
    def on_hide(self, view):
        view.hide_popup()

    def on_hover(self, view, point, hover_zone):
        if hover_zone is not sublime.HOVER_TEXT:
            return
        if not view.score_selector(point, 'source.lsl'):
            return
        if view.settings().get('show_definitions'):
            return

        word = view.substr(view.word(point))
        if not word.isalpha() and not '_' in word:
            return

        from .load_kwdb import KEYWORD_DATA
        if KEYWORD_DATA is None:
            return

        result = KEYWORD_DATA.get(word)
        if result is None:
            return

        tooltip_lines = []
        scope = result.get('scope')
        if scope == 'function' or scope == 'event' or scope == 'constant':
            type = '({}) '.format(result.get('type', 'void')) if scope != 'event' else ''
            params = '()' if scope != 'constant' else ''
            if 'params' in result:
                params = '({})'.format(
                    ', '.join('{} <u>{}</u>'.format(
                        param['type'], param['name']) for param in result['params'])
                )
            value = ' = {}'.format(result['value']) if 'value' in result else ''
            value = value.replace('<' , '&lt;').replace('>', '&gt;')
            tooltip_lines.append('<p>{}<a href="{}{}">{}</a>{}{}</p>'.format(
                type, SL_WIKI_URL, word, word, params, value)
            )
        else:
            tooltip_lines.append('<p><a href="{}{}">{}</a></p>'.format(SL_WIKI_URL, word, word))

        if 'description' in result:
            description = result['description'].replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
            desc_with_links = ''
            words = description.split()
            for desc_word in words:
                desc_word_nopunct = desc_word.translate(str.maketrans('', '', '.,()'))
                link = KEYWORD_DATA.get(desc_word_nopunct)
                if link is not None and (link.get('scope') == 'function' or link.get('scope') == 'constant'):
                    if desc_word[0] in ['(']:
                        desc_with_links += '('
                    desc_with_links += ('<a href="' + SL_WIKI_URL + desc_word_nopunct
                        + '">' + desc_word_nopunct + '</a>')
                    if desc_word[-1] in ['.', ',', ')']:
                        desc_with_links += desc_word[-1]
                else:
                    desc_with_links += desc_word
                desc_with_links += ' '
            tooltip_lines.append('<pre>{}</pre><br><br>'.format(desc_with_links))
        if 'status' in result:
            tooltip_lines.append('<b>Status: {}</b>'.format(result['status']))

        tooltip_text = ' '.join(tooltip_lines)
        view.show_popup(tooltip_text,
            flags=(sublime.COOPERATE_WITH_AUTO_COMPLETE | sublime.HIDE_ON_MOUSE_MOVE_AWAY),
            max_width=800, max_height=512,
            location=point,
            on_hide=self.on_hide(view)
        )
        return
