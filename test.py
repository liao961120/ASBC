#%%
from ASBC.queryDB import Corpus
import ASBC.queryParser as Parser
C = Corpus()

#%%
query = [
    {'tk': '他', 'pos': 'N%'},
    {'tk': '打', 'pos': 'V%'}
]
anchor = {'n': 2, 'seed': 1}
matchOpr = {'token': '=', 'pos': 'LIKE'}
nGram = C.queryNgram(query, anchor, matchOpr)

#%%
import pandas as pd
results = [{}] * nGram.shape[0]
for i, (idx, row) in enumerate(nGram.iterrows()):
    results[i] = C.concordance(row.text_id, row.sent_id, position=(row.position-anchor['seed']), n=anchor['n'])

#%%
#%%
params = {
    'query': '''[word="他" pos=''][word.regex='打' pos='V%']''',
    'left': 10,
    'right': 10
}

params['query'] = Parser.tokenize(params['query'])

#%%
# Find seed token for DB search
score = [ Parser.querySpecificity(q) for q in params['query'] ]
seed_idx = score.index(max(score))
seed_token = params['query'][seed_idx]

anchor = {
    'n': len(params['query']), 
    'seed': seed_idx}
matchOpr = {
    'token': 'REGEXP' if seed_token['tk.regex'] else '=', 
    'pos': 'LIKE'}

if anchor['n'] == 1:
    query = C.queryOneGram(token=seed_token['tk'], pos=seed_token['pos'], matchOpr=matchOpr)
elif anchor['n'] > 1:
    query = C.queryNgram(params['query'], anchor, matchOpr)
#C.queryNgram()


#%%
def _getQueryMatchSet(query, matchOpr):
    out = []
    for q in query:
        # Query DB for matching tags
        matching_tk = []
        matching_pos = []
        if q['tk'] is not None:
            matching_tk = C.conn.execute(f"""
                SELECT token from token WHERE token {matchOpr['token']} ?
                """, (q['tk'] ,) )
        if q['pos'] is not None:
            matching_pos = C.conn.execute(f"""
                SELECT pos from pos WHERE pos {matchOpr['pos']} ?
                """, (q['pos'],) )

        # Convert to python set
        matching_tk = set(t[0] for t in matching_tk)
        matching_pos = set(t[0] for t in matching_pos)
        out.append({'tk': matching_tk, 'pos': matching_pos})
    return out