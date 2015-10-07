import re

import Stemmer

class MyStemmer:
	def __init__(self, language):
		self._language = language

		if language == "EN": 
			language = "english"
		if language == "RU":
			language = "russian"
		if language == "DE":
			language = "german"

		self._stemmer = Stemmer.Stemmer(language)

	def GetStemmsFromSentence(self, sentence):
		words = re.sub("[^\w]", " ", sentence.lower()).split()

		stemmedWords = [self._stemmer.stemWord(w) for w in words]
		stemmedWords = list(set(stemmedWords)) #remove duplicates

#		if self._language == "RU":
#			commonWords = ['в', 'до', 'за', 'из', 'к', 'на', 'о', 'по', 'с', 'со', 'и', 'а', 'но', 'не', 'что', 'у', 'от']
#		if self._language == "EN":
#			commonWords = ['for', 'of', 'the', 'a', 'and']
#		for commonWord in commonWords:
#			stemmedWords = [x for x in stemmedWords if x != commonWord]

		return stemmedWords