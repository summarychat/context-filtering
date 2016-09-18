from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

import argparse
import datetime
import db
import httplib2
import json
import math
import re
import sys

ignored_regexes = ['^l+(o+l+)+$', '^lmao', '^rofl', '^a*(h+a+)*h*$', '^[^a-z0-9]*$']

def get_nlp_service():
    credentials = GoogleCredentials.get_application_default().create_scoped(
        ['https://www.googleapis.com/auth/cloud-platform'])
    http = httplib2.Http()
    credentials.authorize(http)
    return discovery.build('language', 'v1beta1', http=http)

def analyze_all(content, encodingType = 'UTF32'):
	body = {
		'document' : {
			'type' : 'PLAIN_TEXT',
			'content' : content,
		},
		'features' : {
			'extractSyntax' : True,
			'extractDocumentSentiment' : True,
			'extractEntities' : True,
		},
		'encodingType' : encodingType,
	}
	return get_nlp_service().documents().annotateText(body=body).execute()

def score_entities(response):
	return len(response['entities'])

def score_sentiment(response):
	polarity = response['documentSentiment']['polarity']
	magnitude = response['documentSentiment']['magnitude']
	return abs(polarity * magnitude)

def score_token(token):
	# ignore determiners (the, a, an, etc.) and punctuation
	if token['partOfSpeech']['tag'] in ['DET', 'PUNCT']:
		return 0

	# ignore blabber (e.g. lololol)
	for regex in ignored_regexes:
		if re.search(regex, token['text']['content'].lower()) != None:
			return 0

	if token['partOfSpeech']['tag'] == 'NUM':
		return 4

	return 1

def score_complexity(response):
	num_sentences = len(response['sentences'])

	total_score = 0

	for token in response['tokens']:
		total_score += score_token(token)

	return num_sentences * total_score

# does it contain a question?
def score_question(response):
	num_questions = 0
	seen_significant_token = False; # so chained ??? aren't counted as 3 questions

	for token in response['tokens']:
		if seen_significant_token and token['text']['content'] == '?':
			seen_significant_token = False
			num_questions += 1
		elif not seen_significant_token:
			seen_significant_token = score_token(token) != 0

	return num_questions

# look at the distance of the message from the last question
# return a rough probability that this is meant to be an answer
def score_answer(latest_entries):
    latest_entries = db.session().query(db.Message).order_by("timestamp desc").limit(4).all()
    for idx in range(1, len(latest_entries)):
        if score_question(analyze_all(latest_entries[idx].message)):
            return 1/idx

    return 0

def score_elapsed_time(latest_entries):
	if(len(latest_entries) < 2):
		return 0

	elapsed_minutes = (latest_entries[0].timestamp - latest_entries[1].timestamp).total_seconds() / 60

	return min(2 ** (elapsed_minutes / 50), 5) - 1

def scrape(entities):
    str_res = []
    for i in entities:
        try:
            loc_name = i["name"]
            url = i["metadata"]["wikipedia_url"]
        except KeyError:
            continue
        loc_name = loc_name.encode('ascii','ignore')
        url = url.encode('ascii','ignore')
        s = '<a href="'+url+'">'+loc_name+'</a>'
        str_res.append(s)
    final = ','.join(str_res)
    return final

def add_context(chat_room, data):
	latest_entries = db.session().query(db.Message).order_by("timestamp desc").limit(4).all()
	response = analyze_all(data['msg'])

	weights = [30, 10, 7, 30, 20, 5] # entities, sentiment, complexity, question, answer, time
	scores = [score_entities(response), score_sentiment(response), score_complexity(response), score_question(response), score_answer(latest_entries), score_elapsed_time(latest_entries)]

	threshold = 50;
	importance = sum([a * b for a, b in zip(weights, scores)])
	
	#print "response: ", response
	print "entities score: ", scores[0]
	print "sentiment score: ", scores[1]
	print "complexity score: ", scores[2]
	print "question score: ", scores[3]
	print "answer score: ", scores[4]
	print "time score: ", scores[5]
	print "importance: ", importance, 'Yes' if importance > threshold else 'No'

	if importance > threshold:
		db.session().add(db.Event(channel=chat_room, name=data['user'], message=data['msg'], links=scrape(response['entities']), timestamp=latest_entries[0].timestamp))

if __name__ == '__main__':
	for line in open(sys.argv[1]).readlines():
		response = analyze_all(line)
		print response

	

