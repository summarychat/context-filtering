import argparse
from googleapiclient import discovery
import httplib2
import json
from oauth2client.client import GoogleCredentials

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
		},
		'encodingType' : encodingType,
	}
	return getService().documents().annotateText(body=body).execute()

def complexSentence(response):
	numSentences = len(response['sentences'])

def isQuestion(response):
	questionMark = False

	for token in response['tokens']:
		if token['text']['content'] == '?':
			questionMark = True
	return questionMark


if __name__ == '__main__':
	print(analyzeSyntax("where are we?"))

