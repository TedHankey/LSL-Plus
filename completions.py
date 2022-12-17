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
        prev_sep = s_char in '_ '

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
                    ', '.join('${{{}:{} {}}}'.format(idx, param['type'], param['name']) for idx, param in enumerate(result['params'], 1))
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
        elif result.get('scope') == 'entity.name.class.state':
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
        # Find global variables and userfunction names.
        # Loops through lines starting from the top and breaks on encountering
        # the meta.state scope.
        # TODO: store userfunction params so they can be used as a snippet
        
        types = r'(\bfloat|integer|key|list|quaternion|rotation|string|vector\b)'
        regex = r'(?:(?:' + types + R'\s+)(?:\b([A-Za-z_]\w*)\b))'
        
        content = view.substr(sublime.Region(0, loc))
        character_count = 0
        for line in content.split('\n'):
            scope = view.scope_name(character_count)
            character_count += len(line) + 1
            if 'meta.function.lsl' in scope:
                type_vars = re.search(r'(?:((?:' + types + R'\s+)?(?:\b([A-Za-z_]\w*)\b)))(?=\s*\()', line)
                #print('find_variables: userdefs = ', type_vars.groups())
                if fuzzy_match(prefix, type_vars.group(3))[0]:
                    return_value = type_vars.group(2) if type_vars.group(2) else 'void'
                    completions.append(
                    sublime.CompletionItem(
                        trigger = type_vars.group(3),
                        annotation = '(' + return_value + ') function',
                        completion = type_vars.group(3),
                        completion_format = sublime.COMPLETION_FORMAT_TEXT,
                        kind = (sublime.KIND_ID_COLOR_PINKISH, 'f', 'function'),
                        details = 'user defined function'
                    ))
                continue
            elif 'meta.state' in scope:
                break
            elif 'meta.function.body' in scope:
                continue
            else:
                result = re.findall(regex, line)
                if result:
                    for type_vars in result:
                        if type_vars:
                            if fuzzy_match(prefix, type_vars[1])[0]:
                                completions.append(
                                sublime.CompletionItem(
                                    trigger = type_vars[1],
                                    annotation = 'variable',
                                    completion = type_vars[1],
                                    completion_format = sublime.COMPLETION_FORMAT_TEXT,
                                    kind = (sublime.KIND_ID_VARIABLE, 'v', 'variable'),
                                    details = 'global ' + type_vars[0]
                                ))
 
        # Find local and event parameter variables.
        # TODO: remove vars in condional blocks and comments
        region, regions = [], []
        if view.match_selector(loc, 'meta.event.body'):
            region = view.expand_to_scope(loc, 'meta.event.body.lsl')
            regions = view.find_by_selector('meta.event.lsl')
        elif view.match_selector(loc, 'meta.function.body'):
            region = view.expand_to_scope(loc, 'meta.function.body.lsl')
            regions = view.find_by_selector('meta.function.lsl')
        for reg in regions:
            if region.a == reg.b:
                content = view.substr(sublime.Region(reg.a, loc))
                break
        for line in content.split('\n'):
            result = re.findall(regex, line)
            if result:
                for type_vars in result:
                    if type_vars:
                        if fuzzy_match(prefix, type_vars[1])[0]:
                            completions.append(
                            sublime.CompletionItem(
                                trigger = type_vars[1],
                                annotation = 'variable',
                                completion = type_vars[1],
                                completion_format = sublime.COMPLETION_FORMAT_TEXT,
                                kind = (sublime.KIND_ID_VARIABLE, 'v', 'variable'),
                                details = type_vars[0]
                            ))


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
            # Remove 'll' when needed, to stop it counting against the fuzzy match score.
            shortened_word = word
            if word.startswith('ll') and not prefix.startswith('ll'):
                shortened_word = word[2:]
            # Outside of a state.
            if view.match_selector(loc, 'source.lsl - (meta.state, meta.function)'):
                if (result.get('scope') == 'storage.type'
                    or result.get('scope') == 'constant'
                    or result.get('scope') == 'entity.name.class.state'
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
            elif (view.match_selector(loc, 'meta.event.parameters') or
            view.match_selector(loc, 'meta.function.parameters')):
                # Event and userfunction parameters only allow storage types.
                if result.get('scope') == 'storage.type':
                    if fuzzy_match(prefix, word)[0]:
                        item = self.format_result(word, result)
                        completions.append((item))
            # Inside an event or userfunction.
            elif view.match_selector(loc, 'meta.event') or view.match_selector(loc, 'meta.function'):
                # Can't have state or event declaration inside of an event or userfunction.
                if result.get('scope') == 'event' or result.get('scope') == 'entity.name.class.state':
                    continue
                if fuzzy_match(prefix, shortened_word)[0]:
                    item = self.format_result(word, result)
                    completions.append((item))
                    if not looking_for_vars:
                        looking_for_vars = True
                        self.find_variables(view, prefix, loc)
            # DEBUG: Only here to see if we missed a case.
            else:
                print('DEBUG: completions.py: else -> should not get here')
                #sublime.message_dialog('DEBUG: completions.py: else -> should not get here')
                if fuzzy_match(prefix, shortened_word)[0]:
                    item = self.format_result(word, result)
                    completions.append((item))


        completions.sort(key=lambda completion: fuzzy_match(prefix, completion.trigger)[1], reverse=True)

        if completions:
            return (completions, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)

        return None
