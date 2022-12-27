# coding: utf-8

import re

import sublime
import sublime_plugin


# https://github.com/forrestthewoods/lib_fts
# https://gist.github.com/menzenski/f0f846a254d269bd567e2160485f4b89
def fuzzy_match(pattern, instring, adj_bonus=5, sep_bonus=10, camel_bonus=10,
                lead_penalty=-3, max_lead_penalty=-9, unmatched_penalty=-1):
    score, p_idx, s_idx, p_len, s_len = 0, 0, 0, len(pattern), len(instring)
    prev_match, prev_lower = False, False
    prev_sep = True
    best_letter, best_lower, best_letter_idx = None, None, None
    best_letter_score = 0
    matched_indices = []

    while s_idx != s_len:
        p_char = pattern[p_idx] if (p_idx != p_len) else None
        s_char = instring[s_idx]
        p_lower = p_char.lower() if p_char else None
        s_lower, s_upper = s_char.lower(), s_char.upper()

        next_match = p_char and p_lower == s_lower
        rematch = best_letter and best_lower == s_lower

        advanced = next_match and best_letter
        p_repeat = best_letter and p_char and best_lower == p_lower

        if advanced or p_repeat:
            score += best_letter_score
            matched_indices.append(best_letter_idx)
            best_letter, best_lower, best_letter_idx = None, None, None
            best_letter_score = 0

        if next_match or rematch:
            new_score = 0

            if p_idx == 0:
                score += max(s_idx * lead_penalty, max_lead_penalty)

            if prev_match:
                new_score += adj_bonus

            if prev_sep:
                new_score += sep_bonus

            if prev_lower and s_char == s_upper and s_lower != s_upper:
                new_score += camel_bonus

            if next_match:
                p_idx += 1

            if new_score >= best_letter_score:
                if best_letter is not None:
                    score += unmatched_penalty
                best_letter = s_char
                best_lower = best_letter.lower()
                best_letter_idx = s_idx
                best_letter_score = new_score

            prev_match = True

        else:
            score += unmatched_penalty
            prev_match = False

        prev_lower = s_char == s_lower and s_lower != s_upper
        prev_sep = s_char in '_'

        s_idx += 1

    if best_letter:
        score += best_letter_score
        matched_indices.append(best_letter_idx)

    return p_idx == p_len, score


class LSLCompletions(sublime_plugin.EventListener):
    
    def format_result(self, word, result):
        annotation = ''
        completion = ''
        kind_id = sublime.KIND_ID_FUNCTION
        kind_symbol = 'x'
        kind_desc = 'function'

        if result.get('scope') == 'event':
            if 'params' in result:
                completion = '{}({}){}'.format(
                    word,
                    ', '.join('{} {}'.format(param['type'], param['name']) for param in result['params']),
                    '\n{\n\t$0\n}'
                )
            else:
                completion = '{}(){}'.format(
                    word,
                    '\n{\n\t$0\n}'
                )
            annotation = 'event'
            kind_id = sublime.KIND_ID_NAMESPACE
            kind_symbol = 'e'
            kind_desc = 'event'
        elif result.get('scope') == 'function':
            if 'params' in result:
                completion = '{}({})'.format(
                    word,
                    ', '.join('${{{}:{} {}}}'.format(
                        idx, param['type'], param['name']) for idx, param in enumerate(result['params'], 1))
                )
            else:
                completion = '{}()'.format(word)
            if 'type' not in result:
                completion += ';$0'
            annotation = '(' + result.get('type', 'void') + ') function'
            kind_id = sublime.KIND_ID_FUNCTION
            kind_symbol = 'f'
            kind_desc = 'function'
        elif result['scope'].startswith('constant'):
            completion = word
            annotation = result['type'] + ' constant' 
            kind_id = sublime.KIND_ID_MARKUP
            kind_symbol = 'c'
            kind_desc = 'constant'
        elif result.get('scope') == 'storage.type':
            completion = word
            annotation = 'storage type' 
            kind_id = sublime.KIND_ID_TYPE
            kind_symbol = 't'
            kind_desc = 'type'
        elif result.get('scope') == 'keyword.declaration.state':
            completion = word
            if word == 'default':
                completion = 'default\n{\n\t$0\n}'
            annotation = 'state' 
            kind_id = sublime.KIND_ID_NAVIGATION
            kind_symbol = 's'
            kind_desc = 'state'
        elif result['scope'].startswith('keyword.control'):
            completion = word
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
            elif view.match_selector(reg.a, 'meta.state'):
                break
            elif view.match_selector(reg.a, 'meta.function'):
                continue
            elif view.match_selector(reg.a, 'comment'):
                continue
            regions.append(reg)

        for reg in regions:
            type_vars = view.substr(reg).split()
            if fuzzy_match(prefix, type_vars[1])[0]:
                completions.append(
                    sublime.CompletionItem(
                        trigger = type_vars[1],
                        annotation = 'global ' + type_vars[0] + ' variable',
                        completion = type_vars[1],
                        completion_format = sublime.COMPLETION_FORMAT_TEXT,
                        kind = (sublime.KIND_ID_VARIABLE, 'v', 'variable'),
                        details = 'global ' + type_vars[0])
                )

        # Find userfunctions and add the parameters so they can be
        # used in a snippet.
        functions = view.find_by_selector('meta.function.lsl')
        functions_regex = r'(?:(?:' + types + R'\s+)?(?:\b([A-Za-z_]\w*)\b))'
        for function in functions:
            line = view.substr(view.line(function.a))
            result = re.findall(functions_regex, line)
            if fuzzy_match(prefix, result[0][1])[0]:
                return_value = result[0][0] if result[0][0] else 'void'
                completion = '{}({})'.format(
                    result[0][1],
                    ', '.join('${{{}:{} {}}}'.format(
                        idx, type_vars[0], type_vars[1]) for idx, type_vars in enumerate(result[1:], 1))
                )
                completions.append(
                    sublime.CompletionItem(
                        trigger = result[0][1],
                        annotation = '(' + return_value + ') function',
                        completion = completion,
                        completion_format = sublime.COMPLETION_FORMAT_SNIPPET,
                        kind = (sublime.KIND_ID_COLOR_PINKISH, 'f', 'function'),
                        details = 'user defined function')
                )

 
        # Find local and event/userfunction parameter variables.
        #
        # Get a list of regions that match the current location's scope.
        region, regions = [], []
        if view.match_selector(loc, 'meta.event.body'):
            region = view.expand_to_scope(loc, 'meta.event.body.lsl')
            regions = view.find_by_selector('meta.event.lsl')
        elif view.match_selector(loc, 'meta.function.body'):
            region = view.expand_to_scope(loc, 'meta.function.body.lsl')
            regions = view.find_by_selector('meta.function.lsl')


        # Find the start of the region we are interested in.
        reg = sublime.Region(0, 0)
        for reg in regions:
            if reg.b == region.a:
                break

        # If current location is not in the 'body' of an event or userfunction,
        # we get an empty region and would scan the whole file up till the
        # current location. Instead we set the region to the current line and
        # still capture all the variables we're interested in.
        if reg.empty():
            reg = view.line(loc)

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
                    continue
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
            elif (view.match_selector(reg.a, 'comment')
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

        for reg in regions:
            if (view.match_selector(reg.a, 'meta.event.parameters')
                or view.match_selector(reg.a, 'meta.function.parameters')):
                annotation_type = ' parameter'
            else:
               annotation_type = ' variable'
            type_vars = view.substr(reg).split()
            if fuzzy_match(prefix, type_vars[1])[0]:
                completions.append(
                    sublime.CompletionItem(
                        trigger = type_vars[1],
                        annotation = type_vars[0] + annotation_type,
                        completion = type_vars[1],
                        completion_format = sublime.COMPLETION_FORMAT_TEXT,
                        kind = (sublime.KIND_ID_VARIABLE, 'v', 'variable'),
                        details = type_vars[0])
                )

    def on_query_completions(self, view, prefix, locations):
        # Only suggest completions based on the first cursor.
        loc = locations[0]

        if not view.match_selector(loc, 'source.lsl'):
            return None

        if view.match_selector(loc, 'string.quoted.double.lsl'):
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
            # Outside of a state.
            if view.match_selector(loc, 'source.lsl - (meta.state, meta.function)'):
                if (result.get('scope') == 'storage.type'
                    or result.get('scope') == 'constant'
                    or result.get('scope') == 'keyword.declaration.state'
                ):
                    if fuzzy_match(prefix, word)[0]:
                        item = self.format_result(word, result)
                        completions.append((item))
            # Within a state but outside of an event.
            elif view.match_selector(loc, 'meta.state - meta.event'):
                if result.get('scope') == 'event':
                    if fuzzy_match(prefix, word)[0]:
                        item = self.format_result(word, result)
                        completions.append((item))
            # Event and userfunction parameters.
            elif (view.match_selector(loc, 'meta.event.parameters')
                or view.match_selector(loc, 'meta.function.parameters')
            ):
                # Event and userfunction parameters only allow storage types.
                if result.get('scope') == 'storage.type':
                    if fuzzy_match(prefix, word)[0]:
                        item = self.format_result(word, result)
                        completions.append((item))
            # Inside an event or userfunction.
            elif view.match_selector(loc, 'meta.event') or view.match_selector(loc, 'meta.function'):
                # Can't have state or event declaration inside of an event or userfunction.
                if result.get('scope') == 'event' or result.get('scope') == 'keyword.declaration.state':
                    continue
                # Don't suggest constants outside of function parameters
                if (not view.match_selector(loc, 'meta.function-call')
                    and result.get('scope') == 'constant'
                ):
                    continue
                # Function-call arguments.
                if view.match_selector(loc, 'meta.function-call.arguments'):
                    if result.get('scope') == 'keyword':
                        continue
                    # Can't use functions that return nothing.
                    if not result.get('type'):
                        continue
                # Remove 'll' when needed, to stop it counting against the fuzzy match score.
                shortened_word = word
                if word.startswith('ll') and not prefix.startswith('ll'):
                    shortened_word = word[2:]
                if fuzzy_match(prefix, shortened_word)[0]:
                    item = self.format_result(word, result)
                    completions.append((item))
                    if not looking_for_vars:
                        looking_for_vars = True
                        self.find_variables(view, prefix, loc)

        completions.sort(key=lambda completion: fuzzy_match(prefix, completion.trigger)[1], reverse=True)

        if completions:
            return (completions, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)

        return None
