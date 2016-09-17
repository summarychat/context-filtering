import argparse
from googleapiclient import discovery
import httplib2
import json
from oauth2client.client import GoogleCredentials
import re
import sys

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

def scoreComplexity(response):
	numSentences = len(response['sentences'])

	numSignificantTokens = 0

	for token in response['tokens']:
		significant = True

		# ignore determiners and punctuation
		if token['partOfSpeech']['tag'] in ['DET', 'PUNCT']:
			significant = False

		# ignore tokens that are just blabber (i.e. lololol)
		else:
			for regex in open("ignoredRegexes.txt").readlines():
				if re.search(regex, token['text']['content']):
					significant = False
					break

		if significant:
			numSignificantTokens += 1

	return numSentences * numSignificantTokens

def scoreQuestion(response):
	numQuestions = 0

	for token in response['tokens']:
		if token['text']['content'] == '?':
			numQuestions += 1
	return numQuestions

def evaluate(response):
	entities_score = scoreEntities(response)
	sentiment_score = scoreSentiment(response)
	complexity_score = scoreComplexity(response)
	question_score = scoreQuestion(response)

	entities_weight = 30;
	sentiment_weight = 20;
	complexity_weight = 5;
	question_weight = 30;
	
	#print "response: ", response
	print "entities score: ", entities_score
	print "sentiment score: ", sentiment_score
	print "complexity score: ", complexity_score
	print "question score: ", question_score

	important = entities_weight * entities_score + sentiment_weight * abs(sentiment_score) + complexity_weight * complexity_score + question_weight * question_score
	print "important: ", important > 50


if __name__ == '__main__':
	#response = analyzeAll("hello Statue of Liberty :)")
	#response = analyzeAll(sys.argv[1])

	for line in open(sys.argv[1]).readlines():
		response = analyzeAll(line)
		print line
		evaluate(response)

	

