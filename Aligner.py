# -*- coding: utf-8 -*-

import sys
import codecs

import xml.dom.minidom
import xml.etree.ElementTree as ET

import Library
import Dictionary
import MyStemmer
import DynamicProgramming

class Aligner:
	def __init__(self, firstLang, secondLang, firstDictionary, secondDictionary):
		self._firstLang = firstLang
		self._secondLang = secondLang
		self._firstDictionary = firstDictionary
		self._secondDictionary = secondDictionary

	def AlignBooks(self, firstLangBook, secondLangBook):
		alignedMultiText = AlignedMultiText()
		alignedMultiText.AlignedMultiChapters = []
	
		firstLangChapters = firstLangBook.GetContentFromFile().Chapters
		secondLangChapters = secondLangBook.GetContentFromFile().Chapters
		chaptersAlignment = self._alignBooksChapters(firstLangChapters, secondLangChapters)
		for chaptersAlignmentPoint in chaptersAlignment.Points:
			alignedMultiChapter = AlignedMultiChapter()
			alignedMultiChapter.AlignedMultiParapraphs = []
	
			firstLangParagraphs = []
			for index in chaptersAlignmentPoint.FirstLangIndices:
				firstLangParagraphs.extend(firstLangChapters[index].Paragraphs)
			secondLangParagraphs = []
			for index in chaptersAlignmentPoint.SecondLangIndices:
				secondLangParagraphs.extend(secondLangChapters[index].Paragraphs)
			alignedParagraphs = self._alignBookParagraphs(firstLangParagraphs, secondLangParagraphs)
			for alignedParagraph in alignedParagraphs:
				alignedMultiParagraph = AlignedMultiParagraph()
				alignedMultiParagraph.AlignedMultiSentences = []
	
				firstLangParagraph = alignedParagraph[0]
				secondLangParagraph = alignedParagraph[1]
				alignedSentences = self._alignBookSentences(firstLangParagraph.Sentences, secondLangParagraph.Sentences)
				for alignedSentence in alignedSentences:
					alignedMultiSentence = AlignedMultiSentence()
	
					firstLangSentence = alignedSentence[0]
					secondLangSentence = alignedSentence[1]
	
					alignedMultiSentence.FirstLangSentence = firstLangSentence
					alignedMultiSentence.SecondLangSentence = secondLangSentence
					alignedMultiSentence.AlignmentValue = self._getSencencesAlignmentValue(firstLangSentence, secondLangSentence)
	
					alignedMultiParagraph.AlignedMultiSentences.append(alignedMultiSentence)
				alignedMultiChapter.AlignedMultiParapraphs.append(alignedMultiParagraph)
			alignedMultiText.AlignedMultiChapters.append(alignedMultiChapter)
	
		return alignedMultiText 
	
	
	
	def _getSencencesAlignmentValue(self, firstSentence, secondSentence):
		print('Getting sentences alignment value')
		stemmer = MyStemmer.MyStemmer(self._firstLang)
		firstStemms = stemmer.GetStemmsFromSentence(firstSentence)
		stemmer = MyStemmer.MyStemmer(self._secondLang)
		secondStemms = stemmer.GetStemmsFromSentence(secondSentence)
		firstStemmsCount = len(firstStemms)
		secondStemmsCount = len(secondStemms)
	
		if firstStemmsCount == 0 or secondStemmsCount == 0:
			return 0.0

		probability1 = 0.0
		for firstStemm in firstStemms:
			maxProbability = 0.0
			maxProbabilitySecondStemm = "None"
			for secondStemm in secondStemms:
				currProbability = self._firstDictionary.GetTranslationProbability(firstStemm, secondStemm) * self._secondDictionary.GetTranslationProbability(secondStemm, firstStemm)
				if currProbability > maxProbability:
					maxProbability = currProbability
					maxProbabilitySecondStemm = secondStemm
			#print(firstStemm, maxProbability)
			probability1 += maxProbability
			#print('First stemm: ', firstStemm, '. Max probability second stemm: ', maxProbabilitySecondStemm, '. Probability: ', maxProbability, '.')
		probability1 = probability1 / firstStemmsCount
	
		probability2 = 0.0
		for secondStemm in secondStemms:
			maxProbability = 0.0
			maxProbabilityFirstStemm = "None"
			for firstStemm in firstStemms:
				currProbability = self._secondDictionary.GetTranslationProbability(secondStemm, firstStemm) * self._firstDictionary.GetTranslationProbability(firstStemm, secondStemm)
				if currProbability > maxProbability:
					maxProbability = currProbability
					maxProbabilityFirstStemm = firstStemm
			#print(secondStemm, maxProbability)
			probability2 += maxProbability
			#print('Second stemm: ', secondStemm, '. Max probability first stemm: ', maxProbabilityFirstStemm, '. Probability: ', maxProbability, '.')
		probability2 = probability2 / secondStemmsCount
	
		probability = (probability1 + probability2) / 2
	
		return probability
	
	def _alignBooksChapters(self, firstLangChapters, secondLangChapters):
		print('Getting chapters alignment')
		sMatrixRows = len(firstLangChapters)
		sMatrixCols = len(secondLangChapters)
		similarityMatrix = [[0 for x in range(sMatrixCols)] for x in range(sMatrixRows)]
		for i in range(sMatrixRows):
			for j in range(sMatrixCols):
				similarityMatrix[i][j] = int(self._getChaptersSimilarity(firstLangChapters[i], secondLangChapters[j]) * 1000)
		#print(similarityMatrix)
		alignmentIndices = DynamicProgramming.GetAlignmentBySimilarityMatrix(similarityMatrix)
		print(alignmentIndices)

		alignment = Alignment()
		for i in range(len(alignmentIndices)):
			if i < len(alignmentIndices) - 1:
				nextFirstIndex = alignmentIndices[i + 1][0]
				nextSecondIndex = alignmentIndices[i + 1][1]
			else:
				nextFirstIndex = len(firstLangChapters) - 1
				nextSecondIndex = len(secondLangChapters) - 1
			point = AlignmentPoint()
			point.FirstLangIndices = range(alignmentIndices[i][0], nextFirstIndex)
			point.SecondLangIndices = range(alignmentIndices[i][1], nextSecondIndex)
			alignment.Points.append(point)

		return alignment

		#count = min(len(firstLangChapters), len(secondLangChapters))
		#print("ch " + str(len(firstLangChapters) - len(secondLangChapters)))
		#chaptersAlignment = Alignment()
		
		#firstLengths = [len(c.Paragraphs) for c in firstLangChapters]
		#secondLengths = [len(c.Paragraphs) for c in secondLangChapters]
	
		#print(firstLengths)
		#print(secondLengths)
	
		#chaptersAlignment = self._getAlignmentByLengths(firstLengths, secondLengths)
	
		#print(firstLengths)
		#print(secondLengths)
	
	
		#chaptersAlignment.Points = []
		#for i in range(count):
		#	point = AlignmentPoint()
		#	point.FirstLangIndices = [i]
		#	point.SecondLangIndices = [i]
		#	chaptersAlignment.Points.append(point)
		#return chaptersAlignment

	def _getChaptersSimilarity(self, firstChapter, secondChapter):
		count = min(5, len(firstChapter.Paragraphs), len(secondChapter.Paragraphs))
		similarity = 0
		for i in range(count):
			similarity += self._getParagraphSimilarity(firstChapter.Paragraphs[i], secondChapter.Paragraphs[i])
		similarity = similarity / count
		return similarity

	def _getParagraphSimilarity(self, firstParagraph, secondParagraph):
		count = min(5, len(firstParagraph.Sentences), len(secondParagraph.Sentences))
		similarity = 0
		for i in range(count):
			similarity += self._getSencencesAlignmentValue(firstParagraph.Sentences[i], secondParagraph.Sentences[i])
		similarity = similarity / count
		return similarity
	
	def _alignBookParagraphs(self, firstLangParagraphs, secondLangParagraphs):
		print('Getting paragraphs alignment')

		while(len(firstLangParagraphs) != len(secondLangParagraphs) and len(firstLangParagraphs) > 0 and len(secondLangParagraphs) > 0):
			print(len(firstLangParagraphs), len(secondLangParagraphs))
			if (len(firstLangParagraphs) < len(secondLangParagraphs)):
				secondLangParagraphs = self._mergeTwoExtraParagraphs(firstLangParagraphs, secondLangParagraphs)
			else:
				firstLangParagraphs = self._mergeTwoExtraParagraphs(secondLangParagraphs, firstLangParagraphs)
	
		count = min(len(firstLangParagraphs), len(secondLangParagraphs))
		alignedParagraphs = []
		for i in range(count):
			alignedParagraphs.append([firstLangParagraphs[i], secondLangParagraphs[i]])
		return alignedParagraphs
	
	#Объединяет два параграфа из второго списка в один на основании длин параграфов
	def _mergeTwoExtraParagraphs(self, paragraphs1, paragraphs2):
		print('Merging extra paragraphs')

		index = 0
		maxDiff = 0
		for i, paragraph1 in enumerate(paragraphs1):
			diff = len(paragraph1.Sentences) - len(paragraphs2[i].Sentences)
			if diff > maxDiff and i != (len(paragraphs2) - 1):
				maxDiff = diff
				index = i
	
		newParagraphs2 = []
		k = 0
		for i, paragraph2 in enumerate(paragraphs2):
			if (i == index + 1):
				newParagraphs2[i - 1].Sentences += paragraphs2[i].Sentences
			else:
				newParagraphs2.append(paragraphs2[i])
	
		return newParagraphs2
	
	
	def _alignBookSentences(self, firstLangSentences, secondLangSentences):
		print('Getting sentences alignment')

		count = min(len(firstLangSentences), len(secondLangSentences))
		alignedSentences = []
		for i in range(count):
			alignedSentences.append([firstLangSentences[i], secondLangSentences[i]])
		return alignedSentences
	
	def _getAlignmentByLengths(self, firstLengths, secondLengths):
		count = min(len(firstLengths), len(secondLengths))
	
		alignment = Alignment()
		alignment.Points = []
		for i in range(count):
			point = AlignmentPoint()
			point.FirstLangIndices = [i]
			point.SecondLangIndices = [i]
			alignment.Points.append(point)
	
		if len(firstLengths) > len(secondLengths):
			print('lala')
			while len(firstLengths) != len(secondLengths):
				print(firstLengths)
				print(secondLengths)
	
				maxDiffIndex = self._findMaxDifferenceIndex(firstLengths, secondLengths)
				firstLengths[maxDiffIndex] += firstLengths[maxDiffIndex + 1]
				del firstLengths[maxDiffIndex + 1]
				alignment.Points[maxDiffIndex].FirstLangIndices.append(maxDiffIndex + 1)
				for i in range(maxDiffIndex + 1, count):
					point = alignment.Points[i]
					for j in range(len(point.FirstLangIndices)):
						point.FirstLangIndices[j] += 1
	
		return alignment
	
	def _findMaxDifferenceIndex(self, firstArray, secondArray):
		index = 0
		maxDiff = 0
	
		count = min(len(firstArray), len(secondArray))
		for i in range(count):
			diff = secondArray[i] - firstArray[i]
			if diff > maxDiff:
				index = i
				maxDiff = diff
	
		return index

class AlignedMultiText:
	def __init__(self):
		self.AlignedMultiChapters = None

	def SaveToFile(self, path):
		alignedTextElement = ET.Element("aligned_text")
		alignedChaptersElement = ET.Element("aligned_mchapters")
		for alignedMultiChapter in self.AlignedMultiChapters:
			alignedChapterElement = ET.Element("aligned_chapter")
			alignedParagraphsElement = ET.Element("aligned_paragraphs")
			for alignedMultiParagraph in alignedMultiChapter.AlignedMultiParapraphs:
				alignedParagraphElement = ET.Element('aligned_paragraph')
				alignedSentencesElement = ET.Element('aligned_sentences')
				for alignedMultiSentence in alignedMultiParagraph.AlignedMultiSentences:
					alignedSentenceElement = ET.Element('aligned_sentence')
					firstSentenceElement = ET.Element('first_lang_sentence')
					firstSentenceElement.text = alignedMultiSentence.FirstLangSentence
					alignedSentenceElement.append(firstSentenceElement)
					secondSentenceElement = ET.Element('second_sentence_element')
					secondSentenceElement.text = alignedMultiSentence.SecondLangSentence
					alignedSentenceElement.append(secondSentenceElement)
					alignmentValueElement = ET.Element('alignment_value')
					alignmentValueElement.text = str(alignedMultiSentence.AlignmentValue)
					alignedSentenceElement.append(alignmentValueElement)
					alignedSentencesElement.append(alignedSentenceElement)
				alignedParagraphElement.append(alignedSentencesElement)
				alignedParagraphsElement.append(alignedParagraphElement)
			alignedChapterElement.append(alignedParagraphsElement)
			alignedChaptersElement.append(alignedChapterElement)
		alignedTextElement.append(alignedChaptersElement)

		roughXmlString = ET.tostring(alignedTextElement, encoding="utf-8")

		#Making xml pretty		
		roughXml = xml.dom.minidom.parseString(roughXmlString) 
		pretty_xml_as_string = roughXml.toprettyxml()

		print(path)

		with codecs.open(path, 'w', 'utf-8') as target:
			target.write(pretty_xml_as_string)

	def LoadFromFile(self, path):
		print(path)

		self.AlignedMultiChapters = []

		tree = ET.parse(path)
		rootElement = tree.getroot()
		for alignedChapterElement in rootElement.find('aligned_mchapters').findall('aligned_chapter'):
			alignedChapter = AlignedMultiChapter()
			alignedChapter.AlignedMultiParapraphs = []
			for alignedParagraphElement in alignedChapterElement.find('aligned_paragraphs').findall('aligned_paragraph'):
				alignedParagraph = AlignedMultiParagraph()
				alignedParagraph.AlignedMultiSentences = []
				for alignedSentenceElement in alignedParagraphElement.find('aligned_sentences').findall('aligned_sentence'):
					alignedSentence = AlignedMultiSentence()
					alignedSentence.FirstLangSentence = alignedSentenceElement.find('first_lang_sentence').text
					alignedSentence.SecondLangSentence = alignedSentenceElement.find('second_sentence_element').text
					alignedSentence.AlignmentValue = float(alignedSentenceElement.find('alignment_value').text)
					alignedParagraph.AlignedMultiSentences.append(alignedSentence)
				alignedChapter.AlignedMultiParapraphs.append(alignedParagraph)
			self.AlignedMultiChapters.append(alignedChapter)


class AlignedMultiChapter:
	def __init__(self):
		self.FirstLangChapterNames = None
		self.SecondLangChapterNames = None
		self.AlignedMultiParapraphs = None

class AlignedMultiParagraph:
	def __init__(self):
		self.AlignedMultiSentences = None

class AlignedMultiSentence:
	def __init__(self):
		self.FirstLangSentence = None
		self.SecondLangSentence = None
		self.AlignmentValue = None

class AlignedCorpus:
	def __init__(self):
		self.AlignedMultiSentences = None

	def SaveToFile(self, path):
		corpusElement = ET.Element("corpus")
		for alignedSentence in self.AlignedMultiSentences:
			alignedSentenceElement = ET.Element('aligned_sentence')
			firstLangSentenceElement = ET.Element('first_lang_sentence')
			firstLangSentenceElement.text = alignedSentence.FirstLangSentence
			alignedSentenceElement.append(firstLangSentenceElement)
			secondLangSentenceElement = ET.Element('second_lang_sentence')
			secondLangSentenceElement.text = alignedSentence.SecondLangSentence
			alignedSentenceElement.append(secondLangSentenceElement)
			alignmentValueElement = ET.Element('alignment_values')
			alignmentValueElement.text = str(alignedSentence.AlignmentValue)
			alignedSentenceElement.append(alignmentValueElement)
			corpusElement.append(alignedSentenceElement)

		roughXmlString = ET.tostring(corpusElement, encoding="utf-8")

		#Making xml pretty		
		roughXml = xml.dom.minidom.parseString(roughXmlString) 
		pretty_xml_as_string = roughXml.toprettyxml()

		print(path)

		with codecs.open(path, 'w', 'utf-8') as target:
			target.write(pretty_xml_as_string)

class Alignment:
	def __init__(self):
		self.Points = []

class AlignmentPoint:
	def __init__(self):
		self.FirstLangIndices = []
		self.SecondLangIndices = []

def MakeAlignedCorpus(alignedTexts):
	corpus = AlignedCorpus()
	corpus.AlignedMultiSentences = []

	alignedSentences = []
	for alignedText in alignedTexts:
		for alignedChapter in alignedText.AlignedMultiChapters:
			for alignedParagraph in alignedChapter.AlignedMultiParapraphs:
				alignedSentences += alignedParagraph.AlignedMultiSentences
	
	
	
	alignedSentences = [a for a in alignedSentences if a.AlignmentValue > 0.05]
	alignedSentences.sort(key = lambda x: x.AlignmentValue, reverse = True)

	corpus.AlignedMultiSentences = alignedSentences
	return corpus