# -*- coding: utf-8 -*-

import sys
import http.client
import codecs
import os
import xml.etree.ElementTree as ET
import xml.dom.minidom
import re

from bs4 import BeautifulSoup

import OnlineLibrary
import HtmlDownloader

class Library:
	def __init__(self):
		self.ParallelBooks = []

	def LoadFromWiki(self):
		#OnlineLibrary.GetBookContentFromReadcentral('Pride and Prejudice')

		enWikiUrls = Library._getEnWikiUrls()
		wikiBooks = Library._getWikiBooks(enWikiUrls)
		books = Library._getBooks(wikiBooks)

		self.ParallelBooks = books

	def _getEnWikiUrls():
		wikiUrls = []

#		conn = http.client.HTTPConnection("en.wikipedia.org")
#		conn.request("GET", "/wiki/The_100_Best_Books_of_All_Time")
#		responce = conn.getresponse()
#		data = responce.read()

#		root = ET.fromstring(data.decode('utf-8'))
#		table = root.find('.//table[@class="wikitable sortable"]')
#		rows = table.findall('tr')
#		for row in rows:
#			print (1)
#			bookElem = row.find('td/i/a')
#			if (bookElem != None):
#				wikiUrl = bookElem.get('href')
#				wikiUrls.append(wikiUrl)

		html = HtmlDownloader.DownloadHtml('en.wikipedia.org', '/wiki/100_Classic_Book_Collection')
		with codecs.open('1.html', 'w', 'utf-8') as target:
			target.write(html)
		soup = BeautifulSoup(html)

		tableElements = soup.find_all('table', attrs={'class':'wikitable sortable'})
		for tableElement in tableElements:
			print(10)
			rowElements= tableElement.find_all('tr')
			for rowElement in rowElements:
				dataElement = rowElement.find('td') 
				if dataElement != None:
					bookElement = dataElement.find('i').find('a')
					if bookElement != None:
						wikiUrl = bookElement['href']
						wikiUrls.append(wikiUrl)

		return list(set(wikiUrls))

	def _getWikiBooks(enWikiUrls):
		wikiBooks = []
		for enWikiUrl in enWikiUrls:
			print('Getting wiki books ', enWikiUrl)
			wikiBook = _WikiBook()
			wikiBook.Pages = []
			wikiBookPage = _WikiBookPage()
			wikiBookPage.Language = 'EN'
			wikiBookPage.WikiUrl = enWikiUrl
			wikiBook.Pages.append(wikiBookPage)

			html = HtmlDownloader.DownloadHtml('en.wikipedia.org', enWikiUrl)
			soup = BeautifulSoup(html)
			
			ruLinkElement = soup.find('li', attrs={'class':'interlanguage-link interwiki-ru'})
			if ruLinkElement != None:
				wikiBookPage = _WikiBookPage()
				wikiBookPage.Language = 'RU'
				wikiBookPage.WikiUrl = ruLinkElement.find('a')['href'].replace('//ru.wikipedia.org', '')
				wikiBook.Pages.append(wikiBookPage)

			deLinkElement = soup.find('li', attrs={'class':'interlanguage-link interwiki-de'})
			if deLinkElement != None:
				wikiBookPage = _WikiBookPage()
				wikiBookPage.Language = 'DE'
				wikiBookPage.WikiUrl = deLinkElement.find('a')['href'].replace('//de.wikipedia.org', '')
				wikiBook.Pages.append(wikiBookPage)

			wikiBooks.append(wikiBook)

		return wikiBooks

	def _getBooks(wikiBooks):
		parallelBooks = []
		print(len(wikiBooks))
		for i, wikiBook in enumerate(wikiBooks):
			print(str(i))
			parallelBook = ParallelBook()
			parallelBook.Books = []
			for wikiBookPage in wikiBook.Pages:
				print(wikiBookPage.WikiUrl)

				book = Book()
				book.Language = wikiBookPage.Language

				html = HtmlDownloader.DownloadHtml(wikiBookPage.Language.lower() + '.wikipedia.org', wikiBookPage.WikiUrl)
				soup = BeautifulSoup(html)
				headingElement = soup.find('h1', attrs={'id', 'firstHeading'})
				book.Title = headingElement.text
				book.Title = re.sub('\(.+\)', '', book.Title)

				parallelBook.Books.append(book)

			parallelBooks.append(parallelBook)

		return parallelBooks

	def _cleanHtmlString(htmlString):
		htmlString = htmlString.replace('&reg;', '')
		return htmlString

	def WriteToFile(self, path):
		libraryElement = ET.Element("library")
		for parallelBook in self.ParallelBooks:
			parallelBookElement = ET.Element('parallel_book')
			for book in parallelBook.Books:
				bookElement = ET.Element('book')
				languageElement = ET.Element('language')
				languageElement.text = book.Language
				bookElement.append(languageElement)
				titleElement = ET.Element('title')
				titleElement.text = book.Title
				bookElement.append(titleElement)
				if book.LocalFilePath != None:
					filepathElement = ET.Element('local_file_path')
					filepathElement.text = book.LocalFilePath
					bookElement.append(filepathElement)
				parallelBookElement.append(bookElement)
			libraryElement.append(parallelBookElement)

		print(path)

		roughXmlString = ET.tostring(libraryElement, encoding="utf-8")

		roughXml = xml.dom.minidom.parseString(roughXmlString) 
		pretty_xml_as_string = roughXml.toprettyxml()

		with codecs.open(path, 'w', 'utf-8') as target:
			target.write(pretty_xml_as_string)

	def LoadFromFile(self, path):
		self.ParallelBooks = []

		tree = ET.parse(path)
		rootElement = tree.getroot()
		for parallelBookElement in rootElement.findall('parallel_book'):
			parallelBook = ParallelBook()
			parallelBook.Books = []
			for bookElement in parallelBookElement.findall('book'):
				book = Book()
				book.Language = bookElement.find('language').text
				book.Title = bookElement.find('title').text
				filepathElement = bookElement.find('local_file_path')
				if filepathElement != None:
					book.LocalFilePath = filepathElement.text
					book.GetContentFromFile()
				parallelBook.Books.append(book)
			self.ParallelBooks.append(parallelBook)

			

class _WikiBook:
	Pages = []

class _WikiBookPage:
	Language = None
	WikiUrl = None

class ParallelBook:
	def __init__(self):
		self.Books = []

class Book:
	def __init__(self):
		self.Language = None
		self.Title = None
		self.LocalFilePath = None
		self.Content = None

	def GetContentFromInternet(self):
		content = None
		if self.Language == 'EN':
			#content = None
			content = OnlineLibrary.GetBookContentFromReadcentral(self.Title)
		elif self.Language == 'RU':
			#content = None
			content = OnlineLibrary.GetBookContentFromLoweread(self.Title)
		elif self.Language == 'DE':
			content = OnlineLibrary.GetBookContentFromGutenbergSpiergel(self.Title)

		self.Content = content
		return content

	def WriteContentToFile(self, content, path):
		contentElement = ET.Element('content')
		for chapter in content.Chapters:
			chapterElement = ET.Element('chapter')
			chapterTitleElement = ET.Element('title')
			chapterTitleElement.text = chapter.Title
			chapterElement.append(chapterTitleElement)
			paragraphsElement = ET.Element('paragraphs')
			for paragraph in chapter.Paragraphs:
				paragraphElement = ET.Element('paragraph')
				for sentence in paragraph.Sentences:
					sentenceElement = ET.Element('sentence')
					sentenceElement.text = sentence
					paragraphElement.append(sentenceElement)
				paragraphsElement.append((paragraphElement))
			chapterElement.append(paragraphsElement)

			contentElement.append(chapterElement)

		roughXmlString = ET.tostring(contentElement, encoding="utf-8")

		roughXml = xml.dom.minidom.parseString(roughXmlString) 
		pretty_xml_as_string = roughXml.toprettyxml()

		with codecs.open(path, 'w', 'utf-8') as target:
			target.write(pretty_xml_as_string)

	def GetContentFromFile(self):
		if self.LocalFilePath == None:
			return None
		if not os.path.exists(self.LocalFilePath):
			return None

		content = BookContent()

		tree = ET.parse(self.LocalFilePath)
		rootElement = tree.getroot()
		for chapterElement in rootElement.findall('chapter'):
			chapter = BookChapter()
			chapter.Title = chapterElement.find('title').text
			for paragraphElement in chapterElement.find('paragraphs').findall('paragraph'):
				paragraph = BookParagraph()
				for sentenceElement in paragraphElement.findall('sentence'):
					sentence = sentenceElement.text
					paragraph.Sentences.append(sentence)
				chapter.Paragraphs.append(paragraph)
			content.Chapters.append(chapter)
		self.Content = content
		return content

class BookContent:
	def __init__(self):
		self.Chapters = []

class BookChapter:
	def __init__(self):
		self.Title = None
		self.Paragraphs = []

class BookParagraph:
	def __init__(self):
		self.Sentences = []



