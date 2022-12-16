# coding: utf-8

import sublime
import sublime_plugin

SL_WIKI = 'https://wiki.secondlife.com/wiki/'


class LslTooltips(sublime_plugin.EventListener):
   
    def on_hide(self, view):
        view.hide_popup()

    def on_hover(self, view, point, hover_zone):
        if hover_zone is not sublime.HOVER_TEXT:
            return
        if view.settings().get('is_widget'):
            return
        if not view.score_selector(point, 'source.lsl'):
            return
        if view.settings().get('show_definitions'):
            return

        word = view.substr(view.word(point))
        if not word:
            return

        from .load_kwdb import KEYWORD_DATA
        if KEYWORD_DATA is None:
            return

        try:
            tooltip_lines = []
            result = KEYWORD_DATA[word]
            if result is None:
                return

            if 'type' in result or word.startswith('ll'):
                return_value = '({}) '.format(result.get('type', 'void'))
                params = '()'
                if 'params' in result:
                    params = '({})'.format(
                        ', '.join('{} <u>{}</u>'.format(
                            param['type'], param['name']) for param in result['params']
                    ))
                elif not word.startswith('ll'):
                    params = ''
                has_value = ' = {}'.format(str(result['value'])) if 'value' in result else ''
                has_value = has_value.replace('<' , '&lt;').replace('>', '&gt;')
                tooltip_lines.append('<p>{}<a href="{}{}">{}</a>{}{}</p>'.format(return_value, SL_WIKI, word, word, params, has_value))
            else:
                tooltip_lines.append('<p><a href="{}{}">{}</a></p>'.format(SL_WIKI, word, word))

            if 'description' in result:
                description = result['description'].replace('<' , '&lt;').replace('>', '&gt;')
                desc_with_links = ''
                words = description.split()
                for desc_word in words:
                    try:
                        desc_word_nopunct = desc_word.translate(str.maketrans('', '', '.,'))
                        link = KEYWORD_DATA[desc_word_nopunct]
                        if link is not None and (link.get('scope') == 'function' or link.get('scope') == 'constant'):
                            desc_with_links += '<a href="' + SL_WIKI + desc_word_nopunct + '">' + desc_word_nopunct + '</a>'
                            if desc_word[-1] in ['.', ',']:
                                desc_with_links += desc_word[-1]
                        else:
                            desc_with_links += desc_word

                    except Exception as e:
                        desc_with_links += desc_word

                    desc_with_links += ' '
                tooltip_lines.append('<pre>{}</pre><br><br>'.format(desc_with_links))
            if 'status' in result:
                tooltip_lines.append('Status: {}'.format(result['status']))
            if 'delay' in result:
                tooltip_lines.append('Delay: {}<br>'.format(str(result['delay'])))
            if 'energy' in result:
                tooltip_lines.append('Energy: {}'.format(str(result['energy'])))

            tooltip_text = ' '.join(tooltip_lines)
            view.show_popup(tooltip_text,
                flags=(sublime.COOPERATE_WITH_AUTO_COMPLETE | sublime.HIDE_ON_MOUSE_MOVE_AWAY),
                max_width=800, max_height=512,
                location=point,
                on_hide=self.on_hide(view)
            )
            return

        except Exception as e:
            view.hide_popup()
