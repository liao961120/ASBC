import falcon
import json
from falcon_cors import CORS
from ASBC.queryDB import Corpus
import ASBC.queryParser as Parser

# Initialize corpus
C = Corpus()
CONCORDANCE_CACHE = []
############  DEBUGGING ##############
print("Corpus Loaded")
############ _DEBUGGING ##############


class oneGram(object):
    def on_get(self, req, resp):
        """Handles GET requests"""
        params = {
            'token': None,
            'pos': None,
            'left': 10,
            'right': 10
        }
        for k, v in req.params.items():
            params[k] = v
        
        if params['token'] is None or params['pos'] is None:
            return
        print("Recieved request!!!")

        # Query DB
        query = C.queryOneGram(token=params['token'], pos=params['pos'])  #token="^試$", pos="V%"
        results = [{}] * query.shape[0]
        # Retrieve Concordance
        for i, (idx, row) in enumerate(query.iterrows()):
            results[i] = C.concordance(text_id=row.text_id, sent_id=row.sent_id, position=row.position, n=1, left=params['left'], right=params['right'])

        # Response to frontend
        print("Sending response...")
        resp.status = falcon.HTTP_200  # This is the default status
        CONCORDANCE_CACHE = json.dumps(results, ensure_ascii=False)
        resp.body = CONCORDANCE_CACHE
        print("Response sent !!!")


class nGram(object):
    def on_get(self, req, resp):
        params = {
            'query': '''[word="" pos=""][pos='' word="他"][word.regex='打' pos='V.*']''',
            'left': '10',
            'right': '10'
        }
        for k, v in req.params.items():
            params[k] = v
        ############ DEBUGGING ##############
        print("Recieved request!!!")
        ############ _DEBUGGING ##############
        
        # Find seed token for DB search
        params['query'] = Parser.tokenize(params['query'])
        score = [ Parser.querySpecificity(q) for q in params['query'] ]
        seed_idx = score.index(max(score))
        seed_token = params['query'][seed_idx]
        anchor = {
            'n': len(params['query']), 
            'seed': seed_idx}
        matchOpr = {
            'token': 'REGEXP' if seed_token['tk.regex'] else '=', 
            'pos': 'REGEXP'}

        # Query Database
        if anchor['n'] == 1:
            query = C.queryOneGram(token=seed_token['tk'], pos=seed_token['pos'], matchOpr=matchOpr)
        elif anchor['n'] > 1:
            query = C.queryNgram(params['query'], anchor)
        else:
            print("Bug at nGram.on_get() line 70 for querying DB")
        
        # Retrieve Concordance
        concord_params = {
            'n': anchor['n'],
            'left': int(params['left']),
            'right': int(params['right'])
        }
        ######## Debugging ##############
        print(params['query'])
        #################################

        results = [{}] * query.shape[0]
        for i, (idx, row) in enumerate(query.iterrows()):
            results[i] = C.concordance(text_id=row.text_id, sent_id=row.sent_id, position=(row.position - anchor['seed']) ,**concord_params)
        
        # Response to frontend
        ############ DEBUGGING ##############
        print("Sending response...")
        ############ _DEBUGGING ##############
        resp.status = falcon.HTTP_200  # This is the default status
        CONCORDANCE_CACHE = json.dumps(results, ensure_ascii=False)
        resp.body = CONCORDANCE_CACHE
        ############ DEBUGGING ##############
        print("Response sent !!!")
        ############ _DEBUGGING ##############



#---------- API settings -----------#
# falcon.API instances are callable WSGI apps
cors = CORS(allow_all_origins=True)  # Allow access from frontend
app = falcon.API(middleware=[cors.middleware])

# Resources are represented by long-lived class instances
#onegram = oneGram()
ngram = nGram()

# things will handle all requests to the '/things' URL path
#app.add_route('/onegram', onegram)
app.add_route('/query', ngram)


if __name__ == '__main__':
    from wsgiref import simple_server

    port = 1420
    print(f"Start serving at http://localhost:{port}")
    httpd = simple_server.make_server('localhost', port, app)
    httpd.serve_forever()