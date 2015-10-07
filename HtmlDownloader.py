import http.client
import requests

def DownloadHtml(sitename, path):
	url = 'http://' + sitename + path
	r = requests.get(url)

	return r.text
	