# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import xml.dom.minidom
import re
import codecs

import MyStemmer

class Dictionary:
	def __init__(self):
		self._words = None

	def LoadFromBibles(self, firstLang, firstBiblePath, secondLang, secondBiblePath):
		firstLangBible = _Bible()
		firstLangBible.Load(firstBiblePath, firstLang)
		secondLangBible = _Bible()
		secondLangBible.Load(secondBiblePath, secondLang)
		self._words = {}
		for i, (firstLangBook, secondLangBook) in enumerate(zip(firstLangBible.Books, secondLangBible.Books)):
			print(str(i) + " " + str(len(firstLangBible.Books)))
			for firstLangChapter, secondLangChapter in zip(firstLangBook.Chapters, secondLangBook.Chapters):
				for firstLangVerse, secondLangVerse in zip(firstLangChapter.Verses, secondLangChapter.Verses):
					for firstLangWord in firstLangVerse.StemmedWords:
						self._addWord(firstLangWord, secondLangVerse.StemmedWords)
		for dictionaryWord in self._words.values():
			for translation in dictionaryWord.Translations.values():
				translation.Probability = translation.Occurences / dictionaryWord.Occurences
		#self._removeCommonWords(firstLang, secondLang)
		self._removeUnnecessaryTranslations()
	
	def WriteToFile(self, path):
		dictionaryElement = ET.Element("dictionary")
		for dictionaryWord in self._words.values():
			dictionaryWordElement = ET.Element("dictionary_word")
			wordElement = ET.Element("word")
			wordElement.text = dictionaryWord.Word
			dictionaryWordElement.append(wordElement)
			occurencesElement = ET.Element('occurences')
			occurencesElement.text = str(dictionaryWord.Occurences)
			dictionaryWordElement.append(occurencesElement)
			translationsElement = ET.Element("translations")
			dictionaryWordElement.append(translationsElement)
			for dictionaryTranslation in dictionaryWord.Translations.values():
				dictionaryTranslationElement = ET.Element("dictionary_translation")
				wordElement = ET.Element("word")
				wordElement.text = dictionaryTranslation.Word
				dictionaryTranslationElement.append(wordElement)
				occurencesElement = ET.Element("occurences")
				occurencesElement.text = str(dictionaryTranslation.Occurences)
				dictionaryTranslationElement.append(occurencesElement)
				translationsElement.append(dictionaryTranslationElement)
			dictionaryElement.append(dictionaryWordElement)

		roughXmlString = ET.tostring(dictionaryElement, encoding="utf-8")

		#Making xml pretty		
		roughXml = xml.dom.minidom.parseString(roughXmlString) 
		pretty_xml_as_string = roughXml.toprettyxml()

		with codecs.open(path, 'w', 'utf-8') as target:
			target.write(pretty_xml_as_string)

	def LoadFromFile(self, path):
		self._words = {}

		tree = ET.parse(path)
		rootElement = tree.getroot()
		for dictionaryWordElement in rootElement.findall('dictionary_word'):
			word = dictionaryWordElement.find('word').text
			dictionaryWord = _DictionaryWord()
			dictionaryWord.Word = word
			dictionaryWord.Occurences = int(dictionaryWordElement.find('occurences').text)
			dictionaryWord.Translations = {}
			for dictionaryTranslationElement in dictionaryWordElement.find('translations').findall('dictionary_translation'):
				translation = dictionaryTranslationElement.find('word').text
				dictionaryTranslation = _DictionaryTranslation()
				dictionaryTranslation.Word = translation
				dictionaryTranslation.Occurences = int(dictionaryTranslationElement.find('occurences').text)
				dictionaryWord.Translations[translation] = dictionaryTranslation
			self._words[word] = dictionaryWord

	def GetTranslationProbability(self, firstWord, secondWord):
		probability = 0.0
		if firstWord in self._words:
			dictionaryWord = self._words[firstWord]
			if secondWord in dictionaryWord.Translations:
				dictionaryTranslation = dictionaryWord.Translations[secondWord]
				probability = dictionaryTranslation.Occurences / dictionaryWord.Occurences 
		return probability


	def _addWord(self, word, translationWords):
		if word in self._words:
			dictionaryWord = self._words[word]
			dictionaryWord.Occurences += 1
			for translationWord in translationWords:
				if translationWord in dictionaryWord.Translations:
					dictionaryTranslation = dictionaryWord.Translations[translationWord]
					dictionaryTranslation.Occurences += 1
				else:
					newDictionaryTranslation = _DictionaryTranslation()
					newDictionaryTranslation.Word = translationWord
					newDictionaryTranslation.Occurences = 1
					dictionaryWord.Translations[translationWord] = newDictionaryTranslation
		else:
			newDictionaryWord = _DictionaryWord()
			newDictionaryWord.Word = word
			newDictionaryWord.Occurences = 1
			newDictionaryWord.Translations = {}
			for translationWord in translationWords:
				newDictionaryTranslation = _DictionaryTranslation()
				newDictionaryTranslation.Word = translationWord
				newDictionaryTranslation.Occurences = 1
				newDictionaryWord.Translations[translationWord] = newDictionaryTranslation
			self._words[word] = newDictionaryWord

	def _removeUnnecessaryTranslations(self):
		for word, dictionaryWord in self._words.items():
			newTranslations = {}
			for i in range(0, 50):
				maxOccurencesWord = self._getMaxOccurencesWord(dictionaryWord.Translations)
				if maxOccurencesWord != None:
					newTranslations[maxOccurencesWord] = dictionaryWord.Translations[maxOccurencesWord]
					del dictionaryWord.Translations[maxOccurencesWord]
			dictionaryWord.Translations = newTranslations

	def _removeCommonWords(self, firstLang, secondLang):
		ruWords = ['в', 'до', 'за', 'из', 'к', 'на', 'о', 'по', 'с', 'со', 'и', 'а', 'но', 'не', 'что', 'у', 'от', 'я', 'мы', 'ты', 'вы', 'он', 'ег', 'котор', 'чтоб', 'сво', 'как', 'их', 'сво']
		enWords = ['for', 'of', 'the', 'a', 'and', 'to', 'in', 'him', 'his', 'i', 'my', 'that', 'with', 'there', 'then']
		
		if firstLang == 'EN':
			firstLangWords = enWords
		if firstLang == 'RU':
			firstLangWords = ruWords
		
		if secondLang == 'RU':
			secondLangWords = ruWords
		if secondLang == 'EN':
			secondLangWords = enWords
		
		for firstLangWord in firstLangWords:
			self._words.pop(firstLangWord, None)
		for word, dictionaryWord in self._words.items():
			for secondLangWord in secondLangWords:
				dictionaryWord.Translations.pop(secondLangWord, None)

	def _getMaxOccurencesWord(self, translations):
		maxOccurencesWord = None
		maxOccurences = 0
		for word, translation in translations.items():
			if translation.Occurences > maxOccurences:
				maxOccurences = translation.Occurences
				maxOccurencesWord = word
		return maxOccurencesWord

class _DictionaryWord:
	def __init__(self):
		self.Word = None
		self.Translations = None
		self.Occurences = None

class _DictionaryTranslation:
	def __init__(self):
		self.Word = None
		self.Occurences = None
		self.Probability = None

class _Bible:
	def __init__(self):
		self.Books = None

	def Load(self, path, language):
		stemmer = MyStemmer.MyStemmer(language)

		tree = ET.parse(path)
		rootElement = tree.getroot()
		self.Books = []
		for bookElement in rootElement.findall("./text/body/div"):
			book = _BibleBook()
			self.Books.append(book)
			book.Chapters = []
			for chapterElement in bookElement.findall("./div"):
				chapter = _BibleChapter()
				book.Chapters.append(chapter)
				chapter.Verses = []
				for verseElement in chapterElement.findall("./seg"):
					verse = _BibleVerse()
					chapter.Verses.append(verse)
					stemmedWords = stemmer.GetStemmsFromSentence(verseElement.text)
					verse.StemmedWords = stemmedWords

class _BibleBook:
	def __init__(self):
		self.Chapters = None

class _BibleChapter:
	def __init__(self):
		self.Verses = None

class _BibleVerse:
	def __init__(self):
		self.StemmedWords = None