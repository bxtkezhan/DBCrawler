from flask import Flask, render_template, request
from watson_developer_cloud import ConversationV1
from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.parse import quote
import cf_deployment_tracker
import os
import json

# Emit Bluemix deployment event
cf_deployment_tracker.track()

conversation = ConversationV1(
    username= os.getenv('WS_USERNAME', '31656627-a102-4ceb-9aa5-4c1c4c89f837'),
    password= os.getenv('WS_PASSWORD', 'f2fEnYUVACp6'),
    version= os.getenv('WS_VERSION', '2017-12-01'))

workspace_id = os.getenv('WS_WORKSPACE_ID', '3b43504b-90f5-4000-b471-c5ebae1f6a90')

app = Flask(__name__)

port = int(os.getenv('PORT', 8000))

def findBoxzLists(keyword):
    if len(keyword.split(' ')) <=1: return '你好'
    url = 'https://movie.douban.com/j/subject_suggest?q=' + quote(keyword.split(' ')[-1])
    resp = urlopen(url)
    text = resp.read().decode()
    content = json.loads(text)
    for i in range(len(content)):
        info_url = content[i]['url']
        info_resp = urlopen(info_url)
        info_html = info_resp.read().decode()
        info_soup = BeautifulSoup(info_html, 'lxml')
        info_content = info_soup.find(attrs={'property': 'v:summary'}).text
        content[i]['info'] = info_content
    '''
    boxzlists = soup.find(attrs={'class': 'boxzlists'})
    boxzlists_pic = boxzlists.find_all(attrs={'class': 'pic'})
    boxzlists_title = boxzlists.find_all(attrs={'class': 'title'})
    boxzlists_price = boxzlists.find_all(attrs={'class': 'price'})
    '''
    return content # zip(boxzlists_pic, boxzlists_title, boxzlists_price)

def sendMessage(message, method='GET'):
    response = conversation.message(
            workspace_id=workspace_id, input={'text': message})
    if method == 'POST':
        intents = response['intents']
        if len(intents) > 0 and intents[0]['intent'] == 'Such':
            input_text = response['input']['text']
            return findBoxzLists(input_text)
    return response['output']['text'][0]

@app.route('/', methods=['GET', 'POST'])
def index():
    message = '你好'
    output = None
    if request.method == 'GET':
        output = sendMessage(message)
    elif request.method == 'POST':
        message = request.form.get('message', '你好')
        output = sendMessage(message, method='POST')
    return render_template('index.html', output=output, isList=type(output) == list)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
