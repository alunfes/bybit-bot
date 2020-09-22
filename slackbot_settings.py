import json
json_dict = json.load(open('./ignore/slack.json', 'r'))
API_TOKEN = json_dict['API_TOKEN']
DEFAULT_REPLY = 'I have no answer for your inquiry.'