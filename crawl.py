#!/usr/bin/env python

import urllib2
import re
from bs4 import BeautifulSoup
from urlparse import urlparse
import pickle

class Crawl(object):
	def __init__(self, url):
		self.url = url

	def makeSoup(self):
		try:
			return BeautifulSoup(urllib2.urlopen(self.url), "html.parser")
		except:
			return None

	def getBaseUrl(self):
		parsedUrl = urlparse(self.url)
		baseUrl = parsedUrl.scheme+"://"+parsedUrl.netloc+"/"
		return baseUrl


class CrawlBrandList(Crawl):
	def __init__(self, url):
		super(CrawlBrandList, self).__init__(url)

	def getBrandUrls(self):
		soup = self.makeSoup();
		if soup is None:
			return list()

		#serve the soup
		brandListBox = soup.findAll("div", {"class" : "brandmenu-v2"})
		brandListBox = brandListBox[0]
		brandListsHtml = brandListBox.findAll("li");

		#extract the urls
		urls = dict()
		for brand in brandListsHtml:
			anchor = brand.find("a")
			urls[str(anchor.text)] = self.url+str(anchor["href"])
		return urls


class CrawlBrand(Crawl):
	def __init__(self, url):
		super(CrawlBrand, self).__init__(url)

	def getAllPageUrls(self):
		pageUrls = list()

		# Adding this url as the first one
		pageUrls.append(self.url)
		baseUrl = self.getBaseUrl()

		soup = self.makeSoup();

		if soup is None:
			return list()

		pageNavDiv = soup.findAll("div", {"class" : "nav-pages"})

		if (len(pageNavDiv)):
			pageNavItems = pageNavDiv[0].findAll("a")
			for pageNav in pageNavItems:
				pageUrls.append(baseUrl+str(pageNav["href"]))

		return pageUrls


class CrawlItemUrls(Crawl):
	def __init__(self, url):
		super(CrawlItemUrls, self).__init__(url)

	# Gives all the item urls on the page
	def getAllItemUrls(self):
		itemUrls = list()
		baseUrl = self.getBaseUrl()

		soup = self.makeSoup()

		if soup is None:
			return itemUrls

		allItemsLi = soup.find("div", {"class":"makers"}).findAll("li")

		for item in allItemsLi:
			itemUrls.append(baseUrl+str(item.find("a")["href"]))
		return itemUrls


class CrawlItem(Crawl):
	def __init__(self, url):
		super(CrawlItem, self).__init__(url)

	def setSoup(self):
		self.soup = self.makeSoup()
		return self.soup is not None

	def processData(self):
		self.details = dict()
		#specList = self.soup.find("div", {"id":"specs-list"})
		tables = self.soup.findAll("table")
		for item in tables:
			type_name = str(item.find("th").text)
			self.details[type_name] = item.findAll("tr")
		#print self.details

	def getItemName(self):
		heading = self.soup.find("h1", {"class" : "specs-phone-name-title"})
		return str(heading.text)

	def getInternalMemorySizeInGB(self):
		memorySize = 0
		try:
			memoryDetails = self.details["Memory"]
			for item in memoryDetails:
				tds = item.findAll("td")
				if str(tds[0].text) == "Internal":
					memoryString = re.findall("(\d*\.?\d+\ MB|\d*\.?\d+\ GB)", str(tds[1].text))
					if len(memoryString):
						memoryString = memoryString[0].split()
						memorySize = float(memoryString[0])
						if memoryString[1] == 'MB':
							memorySize = round(float(memorySize)/1024, 2)
					break
		except:
			pass
		return memorySize

	def getRamSizeInGB(self):
		ramSize = 0
		try:
			ramDetails = self.details["Memory"]
			for item in ramDetails:
				tds = item.findAll("td")
				if str(tds[0].text) == "Internal":
					ramString = re.findall("(\d*\.?\d+\ MB\ RAM|\d*\.?\d+\ GB\ RAM)", str(tds[1].text))
					if len(ramString):
						ramString = ramString[0].split()
						ramSize = float(ramString[0])
						if ramString[1] == 'MB':
							ramSize = round(ramSize/1024, 2)
					break
		except:
			pass
		return ramSize

	def getCameraDetails(self):
		camSize = 0
		try:
			camDetails = self.details["Camera"]
			for item in camDetails:
				tds = item.findAll("td")
				if str(tds[0].text) == "Primary":
					camString = re.findall("(\d*\.?\d+\ MP)", str(tds[1].text))
					if len(camString):
						camString = camString[0].split()
						camSize = float(camString[0])
					break
		except:
			pass
		return camSize

	def getBatterySize(self):
		batSize = 0
		try:
			batDetails = self.details["Battery"]
			for item in batDetails:
				tds = item.findAll("td")
				batString = re.findall("(\d*\.?\d+\ mAh)", str(tds[1].text))
				if len(batString):
					batString = batString[0].split()
					batSize = float(batString[0])
					break
		except:
			pass
		return batSize

	def getPrice(self):
		price = 0
		try:
			priceDetails = self.details["Misc"]
			for item in priceDetails:
				tds = item.findAll("td")
				priceString = re.findall("(\d*\.?\d+\ EUR)", str(tds[1].text))
				if len(priceString):
					priceString = priceString[0].split()
					price = float(priceString[0])
					break
		except:
			pass
		return price

	def getImageUrl(self):
		imgDiv = self.soup.find("div", {"class":"specs-photo-main"})
		imgEl = imgDiv.find("img")
		return imgEl['src']

	def getItemName(self):
		heading = self.soup.find("h1", {"class" : "specs-phone-name-title"})
		return str(heading.text)


if __name__ == '__main__':
	c = CrawlBrandList('http://www.gsmarena.com/')
	brands = c.getBrandUrls()
	allBrandPages = list()

	for key in brands:
		brand = CrawlBrand(brands[key])
		allPages = brand.getAllPageUrls()
		allBrandPages += allPages

	allItemDetails = list()

	for brandPage in allBrandPages:

		itemUrls = CrawlItemUrls(brandPage)
		itemUrlList = itemUrls.getAllItemUrls()

		for itemUrl in itemUrlList:
			try:
				# grab the content from the file
				# if it's there
				f = open('data.pkl', 'rb')
				allItemDetails = pickle.load(f)
				f.close()
			except:
				pass

			itemDetails = dict()
			item = CrawlItem(itemUrl)
			item.setSoup()
			item.processData()
			itemDetails['name'] = item.getItemName()
			itemDetails['memory'] = item.getInternalMemorySizeInGB()
			itemDetails['ram'] = item.getRamSizeInGB()
			itemDetails['camera'] = item.getCameraDetails()
			itemDetails['battery'] = item.getBatterySize()
			itemDetails['price'] = item.getPrice()
			itemDetails['imageUrl'] = item.getImageUrl()
			itemDetails['url'] = itemUrl
			print itemDetails
			allItemDetails.append(itemDetails)

			# save it back
			outputFile = open('data.pkl', 'wb')
			pickle.dump(allItemDetails, outputFile)
			outputFile.close()

	#print allItemDetails
	# Test for one item fetch
	# itemUrl = "http://www.gsmarena.com/lava_iris_atom_x-7765.php"
	# # itemUrl = "http://www.gsmarena.com/pantech_s902-3637.php"
	# # itemUrl = "http://www.gsmarena.com/pantech_burst-4429.php"
	# item = CrawlItem(itemUrl)
	# item.setSoup()
	# item.processData()
	# print item.getInternalMemorySizeInGB()
	# print item.getRamSizeInGB()
	# print item.getCameraDetails()
	# print item.getBatterySize()
	# print item.getPrice()
	# print item.getImageUrl()

	#print allBrandPages
	#test data to fetch item urls
	# allBrandPages = ['http://www.gsmarena.com/samsung-phones-f-9-0-p4.php']





