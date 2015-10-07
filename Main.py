# -*- coding: utf-8 -*-

import os
import html
import http.client
import sys
import shutil

import Dictionary
import Library
import Aligner


import DynamicProgramming


def main():
	#print(len(sys.argv)) 
	if len(sys.argv) == 7 and sys.argv[1] == '-MakeDictionary':
		firstLang = sys.argv[2]
		firstLangBiblePath = sys.argv[3]
		secondLang = sys.argv[4]
		secondLangBiblePath = sys.argv[5]
		dictionariesPath = sys.argv[6]
		MakeDictionary(firstLang, firstLangBiblePath, secondLang, secondLangBiblePath, dictionariesPath)
	if len(sys.argv) == 3 and sys.argv[1] == '-DownloadLibrary':
		path = sys.argv[2]
		DownloadLibrary(path)
	if len(sys.argv) == 7 and sys.argv[1] == '-AlignBooks':
		libraryPath = sys.argv[2]
		firstLang = sys.argv[3]
		secondLang = sys.argv[4]
		dictionariesPath = sys.argv[5]
		alignedBooksPath = sys.argv[6]
		AlignBooks(libraryPath, firstLang, secondLang, dictionariesPath, alignedBooksPath)
	if len(sys.argv) == 4 and sys.argv[1] == '-MakeTwoLangCorpus':
		alignedBooksPath = sys.argv[2]
		corpusPath = sys.argv[3]
		MakeTwoLangCorpus(alignedBooksPath, corpusPath)
	if len(sys.argv) == 1:
		dictionary1 = Dictionary.Dictionary()
		dictionary1.LoadFromFile("C:\\Users\\Bober\\Desktop\\ботва\\8\\Мат СК\\Dictionaries_2\\EN-RU.xml")
		dictionary2 = Dictionary.Dictionary()
		dictionary2.LoadFromFile("C:\\Users\\Bober\\Desktop\\ботва\\8\\Мат СК\\Dictionaries_2\\RU-EN.xml")
		aligner = Aligner.Aligner("EN", "RU", dictionary1, dictionary2)

		enSentence1 = "The emperor of Lilliput, attended by several of the nobility, comes to see the author in his confinement"
		ruSentence1 = "Император Лилипутии в сопровождении многочисленных вельмож приходит навестить автора в его заключении"
		print('-----Computing alignment value fo sentences:')
		print('1. ', enSentence1)
		print('2. ', ruSentence1)
		value1 = aligner._getSencencesAlignmentValue(enSentence1, ruSentence1)

		print(value1)

		enSentence2 = "I took them all in my right hand, put five of them into my coat-pocket; and as to the sixth, I made a countenance as if I would eat him alive"
		ruSentence2 = "Его императорское величество часто обращался ко мне с вопросами, на которые я отвечал ему, но ни он, ни я не понимали ни слова из того, что говорили друг другу"
		print('-----Computing alignment value fo sentences:')
		print('1. ', enSentence2)
		print('2. ', ruSentence2)
		value2 = aligner._getSencencesAlignmentValue(enSentence2, ruSentence2)

		print(value2)


def MakeDictionary(firstLang, firstLangBiblePath, secondLang, secondLangBiblePath, dictionariesPath):
	dictionary = Dictionary.Dictionary()
	val = dictionary.LoadFromBibles(firstLang, firstLangBiblePath, secondLang, secondLangBiblePath)
	dictFilePath = os.path.join(dictionariesPath, firstLang + '-' + secondLang + '.xml')
	print (dictFilePath)
	dictionary.WriteToFile(dictFilePath)

def DownloadLibrary(path):
	if os.path.exists(path): shutil.rmtree(path)
	os.makedirs(path)
	os.makedirs(os.path.join(path, 'texts'))
	os.makedirs(os.path.join(path, 'texts', "EN"))
	os.makedirs(os.path.join(path, 'texts', "RU"))
	os.makedirs(os.path.join(path, 'texts', "DE"))

	library = Library.Library()
	library.LoadFromWiki()
	library.WriteToFile(os.path.join(path, 'library.xml'))

	for i, parallelBook in enumerate(library.ParallelBooks):
		print(i)
		for book in parallelBook.Books:						
			if book.LocalFilePath == None:
				content = book.GetContentFromInternet()
				if content != None:
					filePath = os.path.join(path, 'texts', book.Language, book.Title + '.xml')
					book.WriteContentToFile(content, filePath)
					book.LocalFilePath = filePath
					library.WriteToFile(os.path.join(path, 'library.xml'))

def AlignBooks(libraryPath, firstLang, secondLang, dictionariesPath, alignedBooksPath):
	if os.path.exists(alignedBooksPath): shutil.rmtree(alignedBooksPath)
	os.makedirs(alignedBooksPath)

	library = Library.Library()
	library.LoadFromFile(os.path.join(libraryPath, 'library.xml'))

	parallelBooksToAlign = []
	for parallelBook in library.ParallelBooks:
		hasFirstLangBook = len([b for b in parallelBook.Books if b.Language == firstLang and b.LocalFilePath != None]) == 1
		hasSecondLangBook = len([b for b in parallelBook.Books if b.Language == secondLang and b.LocalFilePath != None]) == 1
		if hasFirstLangBook and hasSecondLangBook:
			parallelBooksToAlign.append(parallelBook)

	dictionary1 = Dictionary.Dictionary()
	dictionary1.LoadFromFile(os.path.join(dictionariesPath, firstLang + '-' + secondLang + '.xml'))
	dictionary2 = Dictionary.Dictionary()
	dictionary2.LoadFromFile(os.path.join(dictionariesPath, secondLang + '-' + firstLang + '.xml'))

	aligner = Aligner.Aligner(firstLang, secondLang, dictionary1, dictionary2)
	for i, parallelBook in enumerate(parallelBooksToAlign):
		print(i)
		alignedBookPath = os.path.join(alignedBooksPath, str(i) + '.xml')
		firstBook = ([b for b in parallelBook.Books if b.Language == firstLang])[0]
		secondBook = ([b for b in parallelBook.Books if b.Language == secondLang])[0]
		alignedBook = aligner.AlignBooks(firstBook, secondBook)
		alignedBook.SaveToFile(alignedBookPath)

def MakeTwoLangCorpus(alignedBooksPath, corpusPath):
	alignedBooks = []
	for alignedBookPath in [os.path.join(alignedBooksPath, x) for x in os.listdir(alignedBooksPath)]:
		alignedBook = Aligner.AlignedMultiText()
		alignedBook.LoadFromFile(alignedBookPath)
		alignedBooks.append(alignedBook)

	corpus = Aligner.MakeAlignedCorpus(alignedBooks)

	corpus.SaveToFile(corpusPath)

	return None

if __name__ == "__main__":
	main()