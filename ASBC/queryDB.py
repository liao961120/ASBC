#%%
import sqlite3

#------- Helpers ----------#
def sentPos2textPos(sent_len_lst, sent_id, position):
    if sent_id == 0:
        return position
    for i in range(sent_id):
        position += sent_len_lst[i]
    return position


#%%
import jsonlines
import re
import pandas as pd

class Corpus():
    """Query corpus from sqlite database
    """

    def __init__(self, db='data/asbc.sqlite', corp="data/asbc_lite.jsonl"):
        def functionRegex(pattern, value):
            pat = re.compile(r"\b" + pattern + r"\b")
            #pat = re.compile(pattern)
            return pat.search(value) is not None
        
        # sqlite corpus
        conn = sqlite3.connect(db)
        conn.create_function("REGEXP", 2, functionRegex)
        # Connection object of sqlite3
        self.conn = conn
        self.cursor = conn.cursor()

        # Get column names of tables
        conn.commit()

        # jsonl corpus path
        with jsonlines.open(corp) as reader:
            self.corp = [text for text in reader]
    

    def queryOneGram(self, token, pos, matchOpr={'token': '=', 'pos': 'REGEXP'}):
        """Query KWIC of one token
        
        Parameters
        ----------
        token : str
            RegEx pattern of the keyword's form.
        pos : str
            SQL ``LIKE`` pattern of the keyword's PoS tag. To search
            for:

            - Nouns, use ``N%``
            - Verbs, use ``V%``
        matchOpr: dict
            The operator ``<opr>`` given to the SQL command in 
            ``WHERE x <opr> pattern``. Could be one of ``=`` (exact match),
            ``REGEXP`` (uses RegEx to match pattern), or 
            ``LIKE`` (uses ``%`` to match pattern).
            Defaults to exact match for ``token`` and sql pattern for ``pos``.

        Returns
        -------
        pandas.DataFrame
            A pandas dataframe for matching keywords and their
            positional information in the corpus.
        """

        if (token is not None) and (pos is not None):
            sqlQuery = f"""
                SELECT id, text_id, sent_id, position, token_id, pos_id FROM oneGram
                    WHERE 
                        (token_id IN (SELECT token_id FROM token 
                                    WHERE token {matchOpr['token']} ?) ) AND
                        (pos_id IN (SELECT pos_id FROM pos 
                                    WHERE pos {matchOpr['pos']} ?) )
            """
            q = (token, pos)
        elif (token is not None) and (pos is None):
            sqlQuery = f"""
                SELECT id, text_id, sent_id, position, token_id, pos_id FROM oneGram
                    WHERE token_id IN 
                        (SELECT token_id FROM token 
                                WHERE token {matchOpr['token']} ?)
            """
            q = (token, )
        elif (token is None) and (pos is not None):
            sqlQuery = f"""
                SELECT id, text_id, sent_id, position, token_id, pos_id FROM oneGram
                    WHERE pos_id IN 
                        (SELECT pos_id FROM pos 
                                WHERE pos {matchOpr['pos']} ?)
            """
            q = (pos, )
        else:
            print("Error in queryDB.py:line 98")
            return 1
        
        rows = self.cursor.execute(sqlQuery, q)
        self.conn.commit()

        return pd.DataFrame(data=rows, columns=['id', 'text_id', 'sent_id', 'position', 'token_id', 'pos_id'])

    def getNgram(self, text_id, sent_id, position, anchor={'n': 4, 'seed': 1}):
        sent = self.corp[text_id][sent_id]
        ngram_idx_start = position - anchor['seed']
        ngram = sent[ngram_idx_start:(ngram_idx_start + anchor['n'])]
        if len(ngram) != anchor['n']:
            return None
        return ngram

    def _getQueryMatchSet(self, query):
        matchOpr = {'token': '=', 'pos': 'REGEXP'}
        out = []
        for q in query:
            if q['tk.regex']:
                matchOpr['token'] = 'REGEXP'
            else:
                matchOpr['token'] = '='
            # Query DB for matching tags
            matching_tk = []
            matching_pos = []
            if q['tk'] is not None:
                matching_tk = self.conn.execute(f"""
                    SELECT token from token WHERE token {matchOpr['token']} ?
                    """, (q['tk'],) )
            if q['pos'] is not None:
                matching_pos = self.conn.execute(f"""
                    SELECT pos from pos WHERE pos {matchOpr['pos']} ?
                    """, (q['pos'],) )

            # Convert to python set
            matching_tk = set(t[0] for t in matching_tk)
            matching_pos = set(t[0] for t in matching_pos)
            out.append({'tk': matching_tk, 'pos': matching_pos})
        return out

    def queryNgram(self, query, anchor={'n': 2, 'seed': 1}):
        # Query Seed Token
        seed_tk = query[anchor['seed']]['tk']
        seed_pos = query[anchor['seed']]['pos']
        if query[anchor['seed']]['tk.regex']:
            matchOpr = {'token': 'REGEXP', 'pos': 'REGEXP'}
        else:
            matchOpr = {'token': '=', 'pos': 'REGEXP'}
        oneGram = self.queryOneGram(token=seed_tk, pos=seed_pos, matchOpr=matchOpr)

        # Scan through ngrams of the seed token
        valid_rows = []
        queryMatchSet = self._getQueryMatchSet(query)
        for idx, row in oneGram.iterrows():
            ngram = self.getNgram(row.text_id, row.sent_id, row.position, anchor)
            if ngram:  # ngram successfully extracted from sent
                valid = True
                for i in range(len(ngram)):
                    ngram_tk = ngram[i][0]
                    ngram_pos = ngram[i][1]
                    # Check whether token and pos match between query ngram and corpus ngram
                    # If user didn't specify token or pos (i.e. None), they are treated
                    # as equal to whatever tokens or tags are in the corpus
                    tk_equal, pos_equal = False, False
                    if (query[i]['tk'] is None) or (ngram_tk in queryMatchSet[i]['tk']):
                        tk_equal = True
                    if (query[i]['pos'] is None) or (ngram_pos in queryMatchSet[i]['pos']):
                        pos_equal = True
                    if not (tk_equal and pos_equal):
                        valid = False
                        break
            else:
                valid = False
            if valid:
                valid_rows.append(idx)
        
        return oneGram.iloc[valid_rows]


    def concordance(self, text_id, sent_id, position, n=1, left=10, right=10):
        """Retrive KWIC from corpus based on positional information.
        
        Parameters
        ----------
        text_id : int
            One of a index of the items (text level of the corpus) in
            the first level of :py:attr:`.corpus`. This is the index
            indicating the order of the texts in the corpus.
        sent_id : int
            One of a index of the items (sentence level of the corpus)
            in the second level of :py:attr:`.corpus`. 
            This is the index indicating the order of the sentences in
            a text.
        position : int
            One of a index of the items (word level of the corpus)
            in the third level of :py:attr:`.corpus`. 
            This is the index indicating the order of the words in
            a sentence.
        n : int, optional
            Keyword length, by default 1
        left : int, optional
            Left context size, in number of tokens, by default 10
        right : int, optional
            Right context size, in number of tokens, by default 10
        
        Returns
        -------
        dict
            A dictionary with:
            
            - ``keyword``: the keyword and its PoS tag
            - ``left`` & ``right``: the left and right context,
            consisting of tokens and their PoS tags.
        """

        full_text = []
        sent_len = []
        for i, sent in enumerate(self.corp[text_id]):
            sent_len.append(len(sent))
            full_text += sent
        
        keyword_idx = sentPos2textPos(sent_len, sent_id, position)
        keyword = full_text[keyword_idx:(keyword_idx + n)]

        return {
            'keyword': keyword,
            'left': full_text[(keyword_idx - left):keyword_idx],
            'right': full_text[(keyword_idx + n):(keyword_idx + n + right)]
        }

