## LSL package for Sublime
[![Requires Sublime Text Build 4074 or later](https://img.shields.io/badge/Sublime%20Text-%3E%3D4074-orange.svg?style=flat-square)](https://www.sublimetext.com)

Syntax highlighting, linting, autocompletion and tooltips for LSL.\
Includes some color themes for .lsl specific syntax coloring.

## Requirements  
* [Sublime Text](https://www.sublimetext.com) `Build 4074` or later.
* [SublimeLinter](https://github.com/sublimelinter/sublimelinter).
* [lslint](https://github.com/Makopo/lslint).  

## Installation  
- Download the [zip](https://github.com/TedHankey/LSL-Plus/archive/refs/heads/main.zip) file.
- Unzip into your packages folder.
- Sublime will download dependencies and prompt you to restart.
- Restart Sublime Text.

## Linting  
Requires the [SublimeLinter](https://github.com/SublimeLinter/SublimeLinter) package and [lslint](https://github.com/Makopo/lslint/releases).\
You can install SublimeLinter through Package Control.
Make sure the lslint binary is in your path or you can add it to SublimeLinter's  [“paths” setting](http://www.sublimelinter.com/en/stable/troubleshooting.html#adding-to-the-paths-setting).

## Settings  
Open the settings via `Preferences > Package Settings > LSL-Plus > Settings` from the main Sublime menu.

**popups**:  
By default Sublime shows a popup for symbol definitions. To be able to show info popups LSL-Plus turns this off for .lsl files by setting "show_definitions" to false.  You can turn this back on if you like, but info popups will not be shown.

**autocomplete**:  
In order to get suggestions inside of snippet fields, both 'auto_complete_commit_on_tab' and 'auto_complete_with_fields' are set to true by default.

**color scheme**:  
Four color schemes are provided, but not active by default. Pick the one you prefer.
