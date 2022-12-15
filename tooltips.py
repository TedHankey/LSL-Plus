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
                return_value = '({}) '.format(result['type']) if 'type' in result else ''
                params = ''
                if 'params' in result:
                    params = '({})'.format(
                        ', '.join('{} <u>{}</u>'.format(
                            param['type'], param['name']) for param in result['params']
                    ))
                else:
                    params = ''
                has_value = ' = {}'.format(str(result['value'])) if 'value' in result else ''
                has_value = has_value.replace('<' , '&lt;').replace('>', '&gt;')
                tooltip_lines.append('<p>{}<a href="{}{}">{}</a>{}{}</p>'.format(return_value, SL_WIKI, word, word, params, has_value))
            else:
                tooltip_lines.append('<p><a href="{}{}">{}</a></p>'.format(SL_WIKI, word, word))

            if 'description' in result:
                description = result['description'].replace('<' , '&lt;').replace('>', '&gt;')
                tooltip_lines.append('<pre>{}</pre><br><br>'.format(description))
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
