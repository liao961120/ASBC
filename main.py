import falcon
import json
from falcon_cors import CORS
from ASBC.queryDB import Corpus
import ASBC.queryParser as Parser

# Initialize corpus
C = Corpus()
print("Corpus Loaded")


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
        for i, (idx, row) in enumerate(query.iterrows()):
            results[i] = C.concordance(text_id=row.text_id, sent_id=row.sent_id, position=row.position, n=1, left=params['left'], right=params['right'])

        print("Sending response...")
        # Response
        resp.status = falcon.HTTP_200  # This is the default status
        #results = {'token': token, 'pos': pos}
        resp.body = json.dumps(results, ensure_ascii=False)
        print("Response sent !!!")


class nGram(object):
    def on_get(self, req, resp):
        params = {
            'query': '''[word="" pos=""][pos='' word="他"][word.regex='^我們$' pos='']''',
            'matchOpr': {'token': '=', 'pos': 'LIKE'},
            'left': 10,
            'right': 10
        }
        for k, v in req.params.items():
            params[k] = v
        
        params['query'] = Parser.tokenize(params['query'])
        
        # Find seed token for DB search
        score = [ Parser.querySpecificity(q) for q in params['query'] ]
        max_ = score.index(max(score))
        C.queryNgram()



#---------- API settings -----------#
# falcon.API instances are callable WSGI apps
cors = CORS(allow_all_origins=True)  # Allow access from frontend
app = falcon.API(middleware=[cors.middleware])

# Resources are represented by long-lived class instances
onegram = oneGram()

# things will handle all requests to the '/things' URL path
app.add_route('/onegram', onegram)


if __name__ == '__main__':
    from wsgiref import simple_server

    port = 1420
    print(f"Start serving at http://localhost:{port}")
    httpd = simple_server.make_server('localhost', port, app)
    httpd.serve_forever()