import argparse
from googleapiclient import discovery
import httplib2
import json
from oauth2client.client import GoogleCredentials
import re
import sys

ignored_regexes = ['^l+(o+l+)+$', '^lmao', '^rofl', '^a*(h+a+)*h*$']

def getService():
    credentials = GoogleCredentials.get_application_default().create_scoped(
        ['https://www.googleapis.com/auth/cloud-platform'])
    http = httplib2.Http()
    credentials.authorize(http)
    return discovery.build('language', 'v1beta1', http=http)

def analyzeEntities(content, encodingType = 'UTF32'):
	body = {
		'document' : {
			'type' : 'PLAIN_TEXT',
			'content' : content,
		},
		'encodingType' : encodingType,
	}
	return getService().documents().analyzeEntities(body=body).execute()

def analyzeSentiment(content, encodingType = 'UTF32'):
	body = {
		'document' : {
			'type' : 'PLAIN_TEXT',
			'content' : content,
		},
		'encodingType' : encodingType,
	}
	return getService().documents().analyzeSentiment(body=body).execute()

def analyzeSyntax(content, encodingType = 'UTF32'):
	body = {
		'document' : {
			'type' : 'PLAIN_TEXT',
			'content' : content,
		},
		'features' : {
			'extract_syntax' : True,
			'extract_document_sentiment' : False,
			'extract_entities' : False,
		},
		'encodingType' : encodingType,
	}
	return getService().documents().annotateText(body=body).execute()

def analyzeAll(content, encodingType = 'UTF32'):
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
	return getService().documents().annotateText(body=body).execute()


def scoreEntities(response):
	return len(response['entities'])

def scoreSentiment(response):
	polarity = response['documentSentiment']['polarity']
	magnitude = response['documentSentiment']['magnitude']
	return polarity * magnitude 

def significantToken(token):
	# ignore determiners (the, a, an, etc.) and punctuation
	if token['partOfSpeech']['tag'] in ['DET', 'PUNCT']:
		return False

	# ignore blabber (e.g. lololol)
	else:
		for regex in ignored_regexes:
			if re.search(regex, token['text']['content'].lower()) != None:
				return False
	return True

def scoreComplexity(response):
	num_sentences = len(response['sentences'])

	num_significant_tokens = 0

	for token in response['tokens']:
		if significantToken(token):
			num_significant_tokens += 1

	return num_sentences * num_significant_tokens

def scoreQuestion(response):
	num_questions = 0
	seen_significant_token = False; # so chained ??? aren't counted as 3 questions

	for token in response['tokens']:
		if seen_significant_token and token['text']['content'] == '?':
			seen_significant_token = False
			num_questions += 1
		elif not seen_significant_token:
			seen_significant_token = significantToken(token)

	return num_questions

# look at the distance of the message from the last question
# return a rough probability that this is meant to be an answer
def scoreAnswer(response):
	dist = 1

	return 1/dist

def evaluateImportance(response):
	entities_score = scoreEntities(response)
	sentiment_score = scoreSentiment(response)
	complexity_score = scoreComplexity(response)
	question_score = scoreQuestion(response)
	answer_score = scoreAnswer(response)

	entities_weight = 30;
	sentiment_weight = 20;
	complexity_weight = 5;
	question_weight = 30;
	answer_weight = 40;

	threshhold = 50;
	
	#print "response: ", response
	print "entities score: ", entities_score
	print "sentiment score: ", sentiment_score
	print "complexity score: ", complexity_score
	print "question score: ", question_score
	print "answer score: ", answer_score

	important = entities_weight * entities_score + sentiment_weight * abs(sentiment_score) + complexity_weight * complexity_score + question_weight * question_score + answer_weight * answer_score
	print "important: ", important, 'Yes' if important > threshhold else 'No'


if __name__ == '__main__':
	#response = analyzeAll("hello Statue of Liberty :)")
	#response = analyzeAll(sys.argv[1])

	for line in open(sys.argv[1]).readlines():
		response = analyzeAll(line)
		print line
		evaluateImportance(response)
		print

	

