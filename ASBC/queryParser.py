import re

#%%
#query = '''[word="" pos=""][pos='' word="他"][word.regex='^我們$' pos='']'''

def tokenize(string):
    # Deal with single exact match of token
    if string.find("[") == -1:
        return [{
            'tk': string,
            'pos': None,
            'tk.regex': False,
        }]

    # Scan through the string to find matching brackets
    tokens = []
    openPos =[]
    depth = 0
    for i, char in enumerate(string):
        if char == '[':
            openPos.append(i)
            depth += 1
        if char == ']':
            start = openPos.pop()
            depth -= 1
            tokens.append({
                'start': start,
                'end': i,
                'inside': string[start+1:i],
                'depth': depth
            })
    # Get matching brackets at first depth level
    tk_pat = re.compile("""word=['"]([^'"]+)['"]""")
    pos_pat = re.compile("""pos=['"]([^'" ]+)['"]""")
    tkRegEx_pat = re.compile("""word.regex=['"]([^'"]+)['"]""")

    output = []
    for tk in tokens:
        if tk['depth'] == 0:
            token = tk_pat.findall(tk['inside'])
            tkRegEx = tkRegEx_pat.findall(tk['inside'])
            token = tkRegEx if tkRegEx else token
            pos = pos_pat.findall(tk['inside'])
            output.append({
                'tk': token[0] if len(token) > 0 else None,
                'pos': pos[0] if len(pos) > 0 else None,
                'tk.regex': True if tkRegEx else False,
            })
    return output

#%%
def querySpecificity(queryObj={'tk': '^我們$', 'pos': 'N%', 'tk.regex': True}):
    status = {
        'token': {
            'has_regEx': False,
            'zh_len': 0
        },
        'pos': {
            'has_wildcard': False,
            'tag_len': 0,
        }
    }
    #-------- Check token pattern --------#
    # List of regEx metacharacters indicating specific pattern
    regEx_meta = ['^', '$', '[', ']', '?' '{', '}', '(', ')', '|']
    if queryObj['tk.regex'] and \
       set(queryObj['tk']).intersection(regEx_meta):
        status['token']['has_regEx'] = True
    # Check chinese character
    if queryObj['tk'] is not None:
        for char in queryObj['tk']:
            if char > u'\u4e00' and char < u'\u9fff':
                status['token']['zh_len'] += 1

    #------ Check pos tag pattern --------#
    if queryObj['pos'] is not None:
        if queryObj['pos'].find('%') != -1:
            status['pos']['has_wildcard'] = True
        for char in queryObj['pos']:
            if re.match('[A-Za-z]', char):
                status['pos']['tag_len'] += 1
    
    return 1.2 * status['token']['zh_len'] + status['token']['has_regEx'] + \
        0.5 * status['pos']['tag_len'] - 0.2 * status['pos']['has_wildcard']

