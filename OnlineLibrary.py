# -*- coding: utf-8 -*-

import os
import sys
import http.client
import codecs
import xml.etree.ElementTree as ET
import re

from bs4 import BeautifulSoup

import Library
import HtmlDownloader

def GetBookContentFromReadcentral(title):
	content = Library.BookContent()
	content.Chapters = []

	path = _getPathToReadcentralBook(title)
	if path == None:
		return None

	chapterPaths = _getReadCentraChapterPaths(path)
	for p in chapterPaths:
		chapter = _getReadcentralBookChapter(p)
		if len(chapter.Paragraphs) != 0:
			content.Chapters.append(chapter)

	return content

def _getPathToReadcentralBook(title):
	path = None

	titleFirstLetter = title[0]
	
	html = HtmlDownloader.DownloadHtml('www.readcentral.com', '/read-online-books/' + titleFirstLetter)


	soup = BeautifulSoup(html)
	tdElements = soup.find_all('td', attrs={'class':'bookindex'})
	for tdElement in tdElements:
		linkElement = tdElement.find('a')
		linkText = linkElement.string.strip()
		if linkText.lower() == title.lower():
			path = linkElement['href']

	return path

def _getReadCentraChapterPaths(path):
	chapterPaths = []

	html = HtmlDownloader.DownloadHtml('www.readcentral.com', path)

	soup = BeautifulSoup(html)
	tdElements = soup.find_all('td', attrs={'class':'bookindex'})
	for tdElement in tdElements:
		linkElement = tdElement.find('a')
		if linkElement != None:
			path = linkElement['href']
			chapterPaths.append(path)

	chapterPaths.sort()
	return chapterPaths

def _getReadcentralBookChapter(path):
	chapter = Library.BookChapter()
	chapter.Paragraphs = []

	html = HtmlDownloader.DownloadHtml('www.readcentral.com', path)

	soup = BeautifulSoup(html)
	pageheadElem = soup.find('div', attrs={'id':'pagehead'})
	chapter.Title = pageheadElem.div.string.strip()

	contentElement = soup.find('div', attrs={'id':'ctl00_contents_book_chapter_content_area'})
	for paragraphElement in contentElement.find_all('p'):		
		paragraphString = ''.join(paragraphElement.strings)
		#paragraphString = re.sub('<[^>]+>', '', paragraphString)
		if paragraphString != None:
			paragraph = Library.BookParagraph()
			paragraph.Sentences = getEnSentencesFromParagraphString(paragraphString)
			if len(paragraph.Sentences) != 0:
				chapter.Paragraphs.append(paragraph)

	return chapter


def GetBookContentFromLoweread(title):
	content = Library.BookContent()
	content.Chapters = []

	bookId = _getLowereadBookId(title)

	if bookId == None:
		return None

	pages = _getLowereadBookPages(bookId)

	content.Chapters = _getLowereadBookChapters(pages)

	return content


def _getLowereadBookId(title):
	bookId = None

	title = title.lower()
	titleFirstLetter = title[0]

	html = HtmlDownloader.DownloadHtml('loveread.ws', '/letter_nav.php?let=' + str((ord(titleFirstLetter) - ord('а')) + 1))

	soup = BeautifulSoup(html)

	booksElement = soup.find('ul', attrs={'class':'let_ul'})   
	if booksElement != None:
		for bookElement in booksElement.find_all('li'):
			if bookElement.a.string.strip().lower() == title.lower():
				bookId = bookElement.a['href'].split('id=')[1]

	return bookId

def _getLowereadBookPages(bookId):
	pages = []
	pageNum = 1
	while True:
		html = HtmlDownloader.DownloadHtml('loveread.ws', '/read_book.php?id=' + bookId + '&p=' + str(pageNum))
		if str(pageNum) != _getLowereadPageNumber(html):
			break 
		pages.append(html)
		pageNum += 1
	return pages

def _getLowereadPageNumber(html):
	soup = BeautifulSoup(html)
	navElement = soup.find('div', attrs={'class':'navigation'})
	currPageElement = navElement.find('span', attrs={'class':'current'})
	pageNum = currPageElement.string
	return pageNum

def _getLowereadBookChapters(pages):
	chapters = []

	currentChapter = Library.BookChapter()
	currentChapter.Title = ''
	currentChapter.Paragraphs = []

	for page in pages:
		soup = BeautifulSoup(page)

		readBookElement = soup.find('td', attrs={'class':'tb_read_book'})
		if readBookElement != None:
			pageContentElement = readBookElement.find('div', attrs={'class':'MsoNormal'}).find('p', attrs={'class':'MsoNormal'})
			for child in pageContentElement.find_all(re.compile('p|div')):
				if child.name == 'div':
					if child.string != None and child.string.strip() != '':
						if len(currentChapter.Paragraphs) != 0:
							chapters.append(currentChapter)
						currentChapter = Library.BookChapter()
						currentChapter.Title = child.string
				if child.name == 'p':
					paragraphString = ''.join(child.strings)
					if paragraphString.strip() != '':
						paragraphString = paragraphString.replace(os.linesep, ' ')
						paragraph = Library.BookParagraph()
						paragraph.Sentences = []
						sentences = paragraphString.replace('!', '.').replace('?', '.').split('.')
						sentences = [s.strip() for s in sentences]
						for sentence in sentences:
							if sentence != "":
								paragraph.Sentences.append(sentence)
						if len(paragraph.Sentences) != 0:
							currentChapter.Paragraphs.append(paragraph)

	return chapters



def GetBookContentFromGutenbergSpiergel(title):
	content = Library.BookContent()
	content.Chapters = []

	bookId = _getGutenbergSpiegelBookId(title)

	if bookId == None:
		return None

	pages = _getGutenbergSpiegelPages(bookId)

	content.Chapters = _getGutenbergSpiegelChapters(pages)

	return content

def _getGutenbergSpiegelBookId(title):
	bookId = None

	title = title.lower()

	indexPageHtml = HtmlDownloader.DownloadHtml('gutenberg.spiegel.de', '/buch')
	indexPageSoup = BeautifulSoup(indexPageHtml)

	booksElements = indexPageSoup.find('div', attrs={'id':'spTeaserColumn'}).find_all('a')
	for bookElement in booksElements:
		if bookElement.string.strip().lower() == title.lower():
			bookId = bookElement['href'].split('/')[2]

	return bookId

def _getGutenbergSpiegelPages(bookId):
	pages = []
	pageNum = 1

	while True:
		pageHtml = HtmlDownloader.DownloadHtml('gutenberg.spiegel.de', '/buch/' + bookId + '/' + str(pageNum))
		if pageNum > 1 and _isGutenbergSpiegelPageEmpty(pageHtml):
			break
		pages.append(pageHtml)
		pageNum += 1

	return pages

def _isGutenbergSpiegelPageEmpty(pageHtml):
	soup = BeautifulSoup(pageHtml)

	chapterHeaderElement = soup.find('div', attrs={'id':'gutenb'}).find('h3')

	if chapterHeaderElement == None:
		return True
	else:
		return False

def _getGutenbergSpiegelChapters(pages):
	chapters = []

	for page in pages:
		soup = BeautifulSoup(page)
		chapter = Library.BookChapter()
		titleElement = soup.find('div', attrs={'id':'gutenb'}).find('h3')
		if titleElement != None:
			chapter.Title = ''.join(titleElement.strings)
		paragraphElements = soup.find('div', attrs={'id':'gutenb'}).find_all('p')
		for paragraphElement in paragraphElements:
			paragraph = Library.BookParagraph()
			paragraphString = ''.join(paragraphElement.strings)
			if paragraphString != None:
				sentences = paragraphString.replace('!', '.').replace('?', '.').split('.')
				paragraph.Sentences = [s.strip() for s in sentences if s.strip() != '']
				if len(paragraph.Sentences) != 0:
					chapter.Paragraphs.append(paragraph)
		if len(chapter.Paragraphs) != 0 and chapter.Title != None:
			chapters.append(chapter)

	return chapters

def getEnSentencesFromParagraphString(paragraphString):
	paragraphString = paragraphString.replace(os.linesep, ' ')

	quotes = [['“', '"'], ['”', '"']]
	for quote in quotes:
		paragraphString = paragraphString.replace(quote[0], quote[1])

	escapes = [['Mr.', '<Mr>'], ['Mrs.', '<Mrs>'], ['."', '<dq>'], ['?"', '<qq>'], ['!"', '<eq>'], [".'", '<dqq>'], ["?'", '<qqq>'], ["!'", '<eqq>'], ['.)', '<dp>'], ['!)', '<ep>'], ['?)', '<qp>']]
	for escape in escapes:
		paragraphString = paragraphString.replace(escape[0], escape[1])
	separators = ['.', '?', '!', '<dq>', '<qq>', '<eq>', '<dqq>', '<qqq>', '<eqq>']
	for separator in separators:
		paragraphString = paragraphString.replace(separator, separator + '|')	
	sentences = paragraphString.split('|')
	for escape in escapes:
		sentences = [s.replace(escape[1], escape[0]) for s in sentences]
	sentences = [s.strip() for s in sentences]

	sentences = [s for s in sentences if s != '']
	return sentences