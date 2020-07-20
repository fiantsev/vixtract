import requests
import websocket
import uuid
from tornado.escape import json_encode, json_decode
from threading import Thread
from time import sleep
import sys
import ast
import re



if(len(sys.argv) == 4):
    user = sys.argv[1]
    code = sys.argv[3].encode().decode('unicode-escape').encode('latin1').decode('utf-8')
    token = sys.argv[2]
else:
    user = 'ivanvakhmyanin'
    code = 'import json\r\nimport urllib.request\r\nACCESS_TOKEN = \'{accessToken}\'\r\nclass DataFrame:\r\n    def __init__(self):\r\n        self.values = []\r\n        self.cols = []\r\n        self.rows = []\r\n        self.colsInfo = []\r\nclass ColInfo():\r\n    def __init__(self, id):\r\n        self.id = id\r\nclass Filter:\r\n    def __init__(self):\r\n        self.values = []\r\n        self.cols = []\r\n        self.rows = []\r\n        self.selected = []\r\nclass OlapFilter(object):\r\n    def __init__(self, guid=\'\', title=\'\', use_excluding=False, selected=[]):\r\n        self.guid = guid\r\n        self.title = title\r\n        self.use_excluding = use_excluding\r\n        self.selected = selected\r\nolap_filters = []\r\n\r\nmy_filter = Filter()\r\nmy_filter.selected = [[\"Москва\", \"2010\"], [\"Казань\", \"2011\"]]\r\nolap_filters.append(OlapFilter(\'Id виджета\', \'Заголовок виджета\', True, [[\"Москва\", \"2010\"], [\"Казань\", \"2011\"]]))\r\n\r\n# %%\r\n# DEBUG ON\r\n# %%\r\n\r\n# Some code...\r\ntest = 1\r\ntest = test +1\r\n\r\n# %%\r\n%%capture cap_out --no-stderr\r\n\r\nclass JsonResultDataFrame:\r\n    def __init__(self):\r\n        self.name = \'\'\r\n        self.data = DataFrame()\r\n        self.selected = DataFrame()\r\n    pass\r\ndata_frame_list = []\r\nfor key,value in dict(locals()).items():\r\n    if (isinstance(value, DataFrame)):\r\n        jsonresult = JsonResultDataFrame()\r\n        jsonresult.name = key\r\n        jsonresult.data = value\r\n        data_frame_list.append(jsonresult)\r\n    elif (isinstance(value, Filter)):\r\n        jsonresult = JsonResultDataFrame()\r\n        jsonresult.name = key\r\n        jsonresult.data.rows = value.rows\r\n        jsonresult.data.cols = value.cols\r\n        jsonresult.data.values = value.values\r\n        jsonresult.selected.rows = value.selected\r\n        data_frame_list.append(jsonresult)\r\nprint(json.dumps(data_frame_list, default=lambda o: o.__dict__), end=\'\')'
    token = '21af02565a384a2183ff4c1103c269b8'

headers = {'Authorization': 'Token '+token}
http_api_url = 'http://localhost:8000/studio/user/'+user+'/api'
ws_api_url = 'ws://localhost:8000/studio/user/'+user+'/api'

uid = uuid.uuid4()

code = code.replace('\r','')

def py2nb(py_str):
    header_comment = '# %%'
    
    # remove leading header comment
    if py_str.startswith(header_comment):
        py_str = py_str[len(header_comment):]

    cells = []
    chunks = py_str.split('\n%s' % header_comment)

    for chunk in chunks:
        cell_type = 'code'
        cell_meta = {}
        if chunk.startswith("'''"):
            chunk = chunk.strip("'\n")
            cell_type = 'markdown'
        else:
        	if chunk.startswith("AUTOCODE"):
        		chunk = chunk.split('\n', 1)[-1]
        		cell_meta = {'jupyter': {'source_hidden' : True}, 'deletable' : False, 'editable' : False}


        cell = {
            'cell_type': cell_type,
            'metadata': cell_meta,
            'source': chunk.splitlines(True)
        }

        if cell_type == 'code':
            cell.update({'outputs': [], 'execution_count': None})

        cells.append(cell)

    notebook = {
        'cells': cells,
        'metadata': {
            'anaconda-cloud': {},
            'kernelspec': {
                'display_name': 'Python 3',
                'language': 'python',
                'name': 'python3'},
            'language_info': {
                'codemirror_mode': {'name': 'ipython', 'version': 3},
                'file_extension': '.py',
                'mimetype': 'text/x-python',
                'name': 'python',
                'nbconvert_exporter': 'python',
                'pygments_lexer': 'ipython3',
                'version': '3.6.1'}},
        'nbformat': 4,
        'nbformat_minor': 1
    }

    return notebook

def nb2py(notebook):
    result = []
    cells = notebook['cells']
    header_comment = '# %%'

    for cell in cells:
        cell_type = cell['cell_type']

        if(cell['metadata'].get('deletable') == False):
        	continue

        if cell_type == 'markdown':
            result.append('%s"""\n%s\n"""'%
                          (header_comment, ''.join(cell['source'])))

        if cell_type == 'code':
            result.append("%s%s" % (header_comment, ''.join(cell['source'])))

    return '\n'.join(result)

notebook = py2nb(code)

newnotebook = {
  "name": 'debug_'+str(uid)+'.ipynb',
  "path": '/debug_'+str(uid)+'.ipynb',
  "type": "notebook",
  "format": "json",
  "content": notebook
}

r = requests.put(http_api_url +'/contents'+'/debug_'+str(uid)+'.ipynb', headers=headers, json=newnotebook)

newsession = { 
    'id':'', 
    'name': 'debug_'+str(uid)+'.ipynb', 
    'path': 'debug_'+str(uid)+'.ipynb', 
    'type': 'notebook', 
    'kernel': { 
        'name' : 'python3'
    } 
}

r = requests.post(http_api_url +'/sessions',params={'token':token}, json=newsession)
session_id = r.json()['id']
kernel_id = r.json()['kernel']['id']

msg_id=''
msg_response=''

def on_message(ws, message):
    global msg_response
    #print('checking ID: '+msg_id)
    #print("received message as {}".format(message))

    msg = json_decode(message)
    
    msg_type = msg['msg_type']

    parent_msg_id = msg['parent_header']['msg_id']
    
    #print('Received message type:'+msg_type+' with parent ID: '+parent_msg_id)
        
    if (msg_type == 'execute_result') and (parent_msg_id == msg_id):
        #print('  Content:', msg['content']['data']['text/plain'])
        msg_response = msg['content']['data']['text/plain']

def on_error(ws, error):
    print("received error as {}".format(error))

def on_close(ws):    
    print("Connection closed")

def poll_output():    
    global msg_id
    global msg_response
    
    if msg_response != '':
        ws.keep_running = False
        return
    
    sleep(1)
    
    msg_id = uuid.uuid4().hex
    ws.send(json_encode({
            'header': {
                'username': '',
                'version': '5.0',
                'session': '',
                'msg_id': msg_id,
                'msg_type': 'execute_request'
            },
            'parent_header': {},
            'channel': 'shell',
            'content': {
                'code': 'cap_out.stdout',
                'silent': False,
                'store_history': False,
                'user_expressions' : {},
                'allow_stdin' : False
            },
            'metadata': {},
            'buffers': {}
        }))
    #print("sent message on open with id: "+msg_id)
    
    sleep(1)
    myThread = Thread(target=poll_output) #, args=(4,))
    myThread.start()
    
def on_open(ws):
    
    myThread = Thread(target=poll_output) #, args=(4,))
    myThread.start()

if __name__ == "__main__":
    #websocket.enableTrace(True)
    ws = websocket.WebSocketApp(ws_api_url +'/kernels/'+kernel_id+'/channels', 
                              header=headers,
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()

r = requests.get(http_api_url +'/contents'+'/debug_'+str(uid)+'.ipynb', headers=headers)
new_code = nb2py(r.json()['content'])
r = requests.delete(http_api_url +'/contents'+'/debug_'+str(uid)+'.ipynb', headers=headers)
r = requests.delete(http_api_url +'/sessions/'+session_id,params={'token':token})
print(repr("CODE: "+new_code))