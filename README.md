## LSL package for Sublime
[![Requires Sublime Text Build 4050 or later](https://img.shields.io/badge/Sublime%20Text-%3E%3D4050-orange.svg?style=flat-square)](https://www.sublimetext.com)

Syntax highlighting, linting, autocompletion and tooltips for LSL.\
Includes some color themes for .lsl specific syntax coloring.

## Requirements  
* [Sublime Text](https://www.sublimetext.com) `Build 4050` or later.
* [SublimeLinter](https://github.com/sublimelinter/sublimelinter).
* [lslint](https://github.com/Makopo/lslint).  

## Installation  
- Download the zip file.
- Unzip into your packages folder.
- Sublime will download dependencies and prompt you to restart.
- Restart Sublime Text.

## Linting  
Requires the [SublimeLinter](https://github.com/SublimeLinter/SublimeLinter) package and [lslint](https://github.com/Makopo/lslint/releases).\
You can install SublimeLinter through Package Control.
Make sure the lslint binary is in your path or you can add it to SublimeLinter's  [“paths” setting](http://www.sublimelinter.com/en/stable/troubleshooting.html#adding-to-the-paths-setting).

The lslint package does not currently offer the latest version in binary form. If you can't compile this yourself then you can download the latest [builtins.txt](https://raw.githubusercontent.com/Makopo/lslint/master/builtins.txt) and put it inside the folder you stored lslint in. You have to remove the first line of builtins.txt or it will NOT be recognized.


## Settings  
Open the settings via `Preferences > Package Settings > LSL-Plus > Settings` from the main Sublime menu.

**popups**:  
By default Sublime shows a popup for symbol definitions. To be able to show info popups LSL-Plus turns this off for .lsl files by setting "show_definitions" to false.  You can turn this back on if you like, but info popups will not be shown.

**autocomplete**:
In order to get suggestions inside of snippet fields you need to set both 'auto_complete_commit_on_tab' and 'auto_complete_with_fields' to true.

**color scheme**:  
Four color schemes are provided, but not active by default. Pick the one you prefer.
