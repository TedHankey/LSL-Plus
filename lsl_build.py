# coding: utf-8

import os
import shutil

import sublime
import sublime_plugin


class LslBuildCommand(sublime_plugin.WindowCommand):

	def run(self, **kwargs):
		var = self.window.extract_variables()
		file_to_parse = var['file_name']

		path = os.path.dirname(shutil.which('lslint'))
		builtins_txt = os.path.join(path, 'builtins.txt')

		if os.path.exists(builtins_txt):
			kwargs["shell_cmd"] = '{} \"{}\" \"{}\"'.format('lslint -i -p -b', builtins_txt, file_to_parse)
		else:
			kwargs["shell_cmd"] = '{} \"{}\"'.format('lslint -i -p', file_to_parse)

		self.window.run_command("exec", kwargs)

