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
def score_answer(response):
        previous_entries = db.session().query(db.Message).order_by("timestamp desc").limit(4).all()
        previous_entries.pop(0)
        distance = 1
        for entry in previous_entries:
                if score_question(analyze_all(entry.message)):
                        return 1/distance
                distance += 1
        return 0

def score_elapsed_time(response):
	previous_entries = db.session().query(db.Message).order_by("timestamp desc").limit(2).all()

	if(len(previous_entries) < 2):
		return 0

	elapsedTime = (previous_entries[0].timestamp - previous_entries[1].timestamp).total_seconds() / 60

	return max(2 ** (elapsedMinutes / 50), 5) - 1

def evaluate_importance(response):
	weights = [30, 10, 5, 35, 30, 5] # entities, sentiment, complexity, question, answer, time
	scores = [score_entities(response), score_sentiment(response), score_complexity(response), score_question(response), score_answer(response), score_elapsed_time(response)]

	threshold = 50;
	
	#print "response: ", response
	print "entities score: ", scores[0]
	print "sentiment score: ", scores[1]
	print "complexity score: ", scores[2]
	print "question score: ", scores[3]
	print "answer score: ", scores[4]

	important = sum([a * b for a, b in zip(weights, scores)])

	print "important: ", important, 'Yes' if important > threshold else 'No'

	if important > threshold:
		db.session()

def add_context(chat_room, data):
	return 0


if __name__ == '__main__':
	#response = analyzeAll("hello Statue of Liberty :)")
	#response = analyzeAll(sys.argv[1])

	for line in open(sys.argv[1]).readlines():
		response = analyze_all(line)
		print line
		evaluate_importance(response)
		print

	

