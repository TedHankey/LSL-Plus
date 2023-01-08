# coding: utf-8

import re

import sublime
import sublime_plugin
from .fts_fuzzy_match import fuzzy_match


class LSLCompletions(sublime_plugin.EventListener):

    def compare_words(self, prefix, word, weight, result):
        # Remove 'll' when needed, to stop it counting against the fuzzy match score.
        shortened_word = word
        if word.startswith('ll') and not prefix.startswith('ll'):
            shortened_word = word[2:]
        accept, score = fuzzy_match(prefix, shortened_word, weight=weight)
        if accept:
            item = self.format_result(word, result)
            completions.append((item, score))
    
    def format_result(self, word, result):
        completion = word
        category = result.get('category')
        if category == 'event':
            if 'parameters' in result:
                completion = '{}({}){}'.format(
                    word,
                    ', '.join('{} {}'.format(param['type'], param['name']) for param in result['parameters']),
                    '\n{\n\t$0\n}'
                )
            else:
                completion = '{}(){}'.format(word, '\n{\n\t$0\n}')
            annotation = 'event'
            kind_id = sublime.KIND_ID_NAMESPACE
            kind_symbol = 'e'
            kind_desc = 'event'
        elif category == 'function':
            if 'parameters' in result:
                completion = '{}({})'.format(
                    word,
                    ', '.join('${{{}:{} {}}}'.format(
                        idx, param['type'], param['name']) for idx, param in enumerate(result['parameters'], 1))
                )
            else:
                completion = '{}()'.format(word)
            if 'type' not in result:
                completion += ';$0'
            annotation = '(' + result.get('type', 'void') + ') function'
            kind_id = sublime.KIND_ID_FUNCTION
            kind_symbol = 'f'
            kind_desc = 'function'
        elif category.startswith('constant'):
            annotation = result['type'] + ' constant' 
            kind_id = sublime.KIND_ID_MARKUP
            kind_symbol = 'c'
            kind_desc = 'constant'
        elif category == 'storage.type':
            annotation = 'storage type' 
            kind_id = sublime.KIND_ID_TYPE
            kind_symbol = 't'
            kind_desc = 'type'
        elif category == 'keyword.declaration.state':
            if word == 'default':
                completion = 'default\n{\n\t$0\n}'
            annotation = 'state' 
            kind_id = sublime.KIND_ID_NAVIGATION
            kind_symbol = 's'
            kind_desc = 'state'
        elif category.startswith('keyword.control'):
            if word == 'if':
                completion = 'if (${1:condition})$0'
            elif word == 'for':
                completion = 'for (${1:start}; ${2:condition}; ${3:step})\n{\n\t${4:// do something}\n}$0'
            elif word == 'do':
                completion = 'do\n{\n\t${2:// do something}\n}\nwhile (${1:condition});$0'
            elif word == 'while':
                completion = 'while (${1:condition})\n{\n\t${2:// do something}\n}$0'
            annotation = 'keyword' 
            kind_id = sublime.KIND_ID_KEYWORD
            kind_symbol = 'k'
            kind_desc = 'keyword'

        description = result.get('description', 'No description')
       
        return sublime.CompletionItem(
                    trigger = word,
                    annotation = annotation,
                    completion = completion,
                    completion_format = sublime.COMPLETION_FORMAT_SNIPPET,
                    kind = (kind_id, kind_symbol, kind_desc),
                    details = description.replace('<' , '&lt;').replace('>', '&gt;')
                )

    def find_variables(self, view, prefix, loc):
        # Find global variables and userfunctions.
        types = r'(\bfloat|integer|key|list|quaternion|rotation|string|vector\b)'
        regex = r'(?:(?:' + types + R'\s+)(?:\b([A-Za-z_]\w*)\b))'
        
        # Find global variables.
        regions = []
        reg = sublime.Region(0, 0)
        pos = 0
        while pos < loc:
            pos = reg.b
            reg = view.find(regex, pos)
            if reg.a > loc or reg.a == -1:
                break
            if view.match_selector(reg.a, 'meta.state'):
                break
            if view.match_selector(reg.a, 'meta.function'):
                continue
            if view.match_selector(reg.a, 'comment'):
                continue
            regions.append(reg)

        for reg in regions:
            type_vars = view.substr(reg).split()
            accept, score = fuzzy_match(prefix, type_vars[1])
            if accept:
                completions.append((
                    sublime.CompletionItem(
                        trigger = type_vars[1],
                        annotation = 'global ' + type_vars[0] + ' variable',
                        completion = type_vars[1],
                        completion_format = sublime.COMPLETION_FORMAT_TEXT,
                        kind = (sublime.KIND_ID_VARIABLE, 'v', 'variable'),
                        details = 'global ' + type_vars[0]
                    ),
                    score
                ))

        # Find userfunctions and add the parameters so they can be
        # used in a snippet.
        functions = view.find_by_selector('meta.function.lsl')
        functions_regex = r'(?:(?:' + types + R'\s+)?(?:\b([A-Za-z_]\w*)\b))'
        for function in functions:
            line = view.substr(view.line(function.a))
            result = re.findall(functions_regex, line)
            accept, score = fuzzy_match(prefix, result[0][1])
            if accept:
                return_value = result[0][0] if result[0][0] else 'void'
                completion = '{}({})'.format(
                    result[0][1],
                    ', '.join('${{{}:{} {}}}'.format(
                        idx, type_vars[0], type_vars[1]) for idx, type_vars in enumerate(result[1:], 1))
                )
                completions.append((
                    sublime.CompletionItem(
                        trigger = result[0][1],
                        annotation = '(' + return_value + ') function',
                        completion = completion,
                        completion_format = sublime.COMPLETION_FORMAT_SNIPPET,
                        kind = (sublime.KIND_ID_COLOR_GREENISH, 'f', 'function'),
                        details = 'user defined function'
                    ),
                    score
                ))

        # Find local and event/userfunction parameter variables.
        #
        # TODO: This can fail when scopes change while we are typing in
        # the source file. May be best to fix in the syntax file.
        # Get a list of regions that match the current location's scope.
        region = []
        if view.match_selector(loc, 'meta.event.body'):
            region = view.expand_to_scope(loc, 'meta.event.body.lsl')
            regions = view.find_by_selector('meta.event.lsl')
        elif view.match_selector(loc, 'meta.function.body'):
            region = view.expand_to_scope(loc, 'meta.function.body.lsl')
            regions = view.find_by_selector('meta.function.lsl')
        else:
            # Current location is not in the 'body' of an event or userfunction.
            # Set the region to the current line so we still capture all the
            # variables we're interested in.
            region = view.line(loc)
            regions = [region]


        # Find the start of the region we are interested in.
        reg = sublime.Region(0, 0)
        for reg in regions:
            if reg.b == region.a:
                break

        # Make a list of blocks that are out of scope.
        blocks = []
        block = sublime.Region(0, 0)
        nesting = 0
        pos = loc
        while pos > reg.a:
            pos -= 1
            if view.substr(pos) == '}' and view.match_selector(pos, 'punctuation'):
                if nesting == 0:
                    block.b = pos
                nesting -= 1
            elif view.substr(pos) == '{' and view.match_selector(pos, 'punctuation'):
                if block.b == 0:
                    continue # Do not change nesting.
                if nesting == -1:
                    block.a = pos
                    blocks.append(block)
                    block = sublime.Region(0, 0)
                nesting += 1

        # Find variables and check if they are within scope.
        regions = []
        pos = reg.a
        while pos < loc:
            reg = view.find(regex, pos)
            if reg.a > loc or reg.a == -1:
                break
            # Skip variables in comments and userfunction declarations.
            if (view.match_selector(reg.a, 'comment')
                or view.match_selector(reg.a, 'meta.function.lsl - meta.function.parameters')
            ):
                pos = reg.b
                continue
            in_scope = True
            for block in blocks:
                if block.contains(reg):
                    in_scope = False
                    break
            if in_scope:
                regions.append(reg)
            pos = reg.b

        # The remaining regions all contain variables local to the current location.
        for reg in regions:
            annotation_type = ' variable'
            if (view.match_selector(reg.a, 'meta.event.parameters')
                or view.match_selector(reg.a, 'meta.function.parameters')
            ):
                annotation_type = ' parameter'
            type_vars = view.substr(reg).split()
            accept, score = fuzzy_match(prefix, type_vars[1])
            if accept:
                completions.append((
                    sublime.CompletionItem(
                        trigger = type_vars[1],
                        annotation = type_vars[0] + annotation_type,
                        completion = type_vars[1],
                        completion_format = sublime.COMPLETION_FORMAT_TEXT,
                        kind = (sublime.KIND_ID_VARIABLE, 'v', 'variable'),
                        details = type_vars[0]
                    ),
                    score
                ))

    def on_query_completions(self, view, prefix, locations):
        # Only suggest completions based on the first cursor.
        loc = locations[0]

        if not view.match_selector(loc, 'source.lsl'):
            return None

        from .load_kwdb import KEYWORD_DATA
        if KEYWORD_DATA is None:
            return None

        global completions
        completions = []
        looking_for_vars = False

        for word, result in KEYWORD_DATA.items():
            # Don't suggest invalid/deprecated completions.
            if result.get('status'):
                continue

            category = result.get('category')
            weight = 0

            # Outside of a state.
            if view.match_selector(loc, 'source.lsl - (meta.state, meta.function)'):
                if (category == 'storage.type'
                    or category == 'constant'
                    or category == 'keyword.declaration.state'
                ):
                    # High chance of using storage types. Add some weight.
                    if category == 'storage.type':
                        weight = 10
                    self.compare_words(prefix, word, weight, result)

            # Within a state but outside of an event.
            elif view.match_selector(loc, 'meta.state - meta.event'):
                if category == 'event':
                    self.compare_words(prefix, word, weight, result)

            # Event and userfunction parameters. Only allow storage types.
            elif (view.match_selector(loc, 'meta.event.parameters')
                or view.match_selector(loc, 'meta.function.parameters')
            ):
                if category == 'storage.type':
                    self.compare_words(prefix, word, weight, result)

            # Inside an event or userfunction.
            elif view.match_selector(loc, 'meta.event') or view.match_selector(loc, 'meta.function'):
                # Can't have state or event declaration inside of an event or userfunction.
                if category == 'event' or category == 'keyword.declaration.state':
                    continue
                # Ignore keywords and void functions in function-call arguments.
                if view.match_selector(loc, 'meta.function-call.arguments'):
                    if category == 'keyword' or not result.get('type'):
                        continue
                # Chances of using a constant outside of a function-call are small.
                # Give it less weight.
                if not view.match_selector(loc, 'meta.function-call.arguments'):
                    if category == 'constant':
                        weight = -10

                self.compare_words(prefix, word, weight, result)
                if not looking_for_vars:
                    looking_for_vars = True
                    self.find_variables(view, prefix, loc)

        completions.sort(key=lambda comp: comp[1], reverse=True)
        completions = [comp for comp, _s in completions]

        if completions:
            return (completions,
                        sublime.INHIBIT_WORD_COMPLETIONS |
                        sublime.DYNAMIC_COMPLETIONS |
                        sublime.INHIBIT_REORDER
                    )

        return None
