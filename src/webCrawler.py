from abc import ABCMeta, abstractmethod
import BeautifulSoup
import urllib2
import sys
import bleach

#################### Root Class (Abstract) ####################
class SkyThoughtCollector(object):
	__metaclass__ = ABCMeta
	baseURLString = "base_url"
	airlinesString = "air_lines"
	limitString = "limits"
	baseURl = ""
	airlines = []
	limit = 10
	
	@abstractmethod
	def collectThoughts(self):
		print "Something Wrong!! You're calling an abstract method"
	
	@classmethod
	def getConfig(self, configpath):
		#print "In get Config"
		config = {}
		conf = open(configpath)
		for line in conf:
			if ("#" not in line):
				words = line.strip().split('=')
				config[words[0].strip()] = words[1].strip()
				#print config
		self.baseURl = config[self.baseURLString]
		if config.has_key(self.airlinesString):
			self.airlines = config[self.airlinesString].split(',')
		if config.has_key(self.limitString):
			self.limit = int(config[self.limitString])
		#print self.airlines
	
	def downloadURL(self, url):
		#print "downloading url"
		req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"})
		pageFile = urllib2.urlopen( req )
		#pageFile = urllib2.urlopen(url)
		if pageFile.getcode() != 200:
			return "Problem in URL"
		pageHtml = pageFile.read()
		pageFile.close()
		return "".join(pageHtml)
		
	def remove_junk(self, arg):
		f = open('junk.txt')
		for line in f:
			arg.replace(line.strip(),'')
		return arg
		
	def print_args(self, args):
		out =''
		last = 0
		for arg in args:
			if args.index(arg) == len(args) -1:
				last = 1
			reload(sys)
			sys.setdefaultencoding("utf-8")
			arg = arg.decode('utf8','ignore').encode('ascii','ignore').strip()
			arg = arg.replace('\n',' ')
			arg = arg.replace('\r','')
			arg = self.remove_junk(arg)
			if last == 0:
				out = out + arg + '\t'
			else:
				out = out + arg
		print out

####################### Airlines Child #######################
class AirLineReviewCollector(SkyThoughtCollector):
	months = ['January', 'February', 'March', 'April', 'May', 
	'June', 'July', 'August', 'September', 'October', 'November', 
	'December' ]
	
	def __init__(self, configpath):
		#print "In Config"
		super(AirLineReviewCollector,self).getConfig(configpath)
	
	def parseSoupHeader(self, header):
		#print "parsing header"
		name = surname = year = month = date = country =''
		txt = header.find("h9")
		words = str(txt).strip().split(' ')
		for j in range(len(words)-1):
			if words[j] in self.months:
				date = words[j-1]
				month= words[j]
				year = words[j+1]
				name = words[j+3]
				surname = words[j+4]
		if ")" in words[-1]:
			country = words[-1].split(')')[0]
		if "(" in country:
			country = country.split('(')[1]
		else:
			country = words[-2].split('(')[1] + country
		return (name, surname, year, month, date, country)

	def parseSoupTable(self, table):
		#print "parsing table"
		images = table.findAll("img")
		over_all = str(images[0]).split("grn_bar_")[1].split(".gif")[0]
		money_value = str(images[1]).split("SCORE_")[1].split(".gif")[0]
		seat_comfort = str(images[2]).split("SCORE_")[1].split(".gif")[0]
		staff_service = str(images[3]).split("SCORE_")[1].split(".gif")[0]
		catering = str(images[4]).split("SCORE_")[1].split(".gif")[0]
		entertainment = str(images[4]).split("SCORE_")[1].split(".gif")[0]
		if 'YES' in str(images[6]):
			recommend = 'YES'
		else:
			recommend = 'NO'
		status = table.findAll("p", {"class":"text25"})
		stat = str(status[2]).split(">")[1].split("<")[0]
		return (stat, over_all, money_value, seat_comfort, staff_service, catering, entertainment, recommend)

	def collectThoughts(self):
		#print "Collecting Thoughts"
		for al in AirLineReviewCollector.airlines:
			count = 0
			while count < AirLineReviewCollector.limit:
				count = count + 1
				url = ''

			if count == 1:
				url = AirLineReviewCollector.baseURl + al + ".htm"
			else:
				url = AirLineReviewCollector.baseURl + al + "_"+str(count)+ ".htm"
			soup = BeautifulSoup.BeautifulSoup(super(AirLineReviewCollector,self).downloadURL(url))
			blogs = soup.findAll("p")
			tables = soup.findAll("table", {"class":"review-ratings"})
			review_headers = soup.findAll("td")
			for i in range(len(tables)-1):
				(name, surname, year, month, date, country) = self.parseSoupHeader(review_headers[i])
				(stat, over_all, money_value, seat_comfort, staff_service, catering, entertainment, recomend) = self.parseSoupTable(tables[i])
				blog = str(blogs[i]).split(">")[1].split("<")[0]
				args = [al, name, surname, year, month, date, country, stat, over_all, money_value, seat_comfort, staff_service, catering, entertainment, 
				recomend, blog]
				super(AirLineReviewCollector,self).print_args(args)

######################## Retail Child ########################
class RetailReviewCollector(SkyThoughtCollector):
	def __init__(self, configpath):
		#print "In Config"
		super(RetailReviewCollector,self).getConfig(configpath)
	
	def collectThoughts(self):
		soup = BeautifulSoup.BeautifulSoup(super(RetailReviewCollector,self).downloadURL(RetailReviewCollector.baseURl))
		lines = soup.findAll("a",{"style": "font-size:15px;"})
		links = []
		for line in lines:
			if ("review" in str(line)) & ("target" in str(line)):
				ln = str(line)
				link = ln.split("href=")[-1].split("target=")[0].replace("\"","").strip()
				links.append(link)
			
		for link in links:
			soup = BeautifulSoup.BeautifulSoup(super(RetailReviewCollector,self).downloadURL(link))
			comment = bleach.clean(str(soup.findAll("div",{"itemprop":"description"})[0]),tags=[], strip=True)
			tables = soup.findAll("table", {"class":"smallfont space0 pad2"})
			parking = ambience = range = economy = product = 0
			for table in tables:
				if "Parking:" in str(table):
					rows = table.findAll("tbody")[0].findAll("tr")
					for row in rows:
						if "Parking:" in str(row):
							parking = str(row).count("read-barfull")
						if "Ambience" in str(row):
							ambience = str(row).count("read-barfull")
						if "Store" in str(row):
							range = str(row).count("read-barfull")
						if "Value" in str(row):
							economy = str(row).count("read-barfull")
						if "Product" in str(row):
							product = str(row).count("smallratefull")
			author = bleach.clean(soup.findAll("span",{"itemprop":"author"})[0], tags=[], strip=True)
			date = soup.findAll("meta",{"itemprop":"datePublished"})[0]["content"]
			args = [date, author,str(parking), str(ambience),str(range), str(economy), str(product), comment]
			super(RetailReviewCollector,self).print_args(args)
	
######################## Main Function ########################
if __name__ == "__main__":
	if sys.argv[1] == 'airline':
		instance = AirLineReviewCollector(sys.argv[2])
		instance.collectThoughts()
	else:
		if sys.argv[1] == 'retail':
			instance = RetailReviewCollector(sys.argv[2])
			instance.collectThoughts()
		else:
			print "Usage is"
			print sys.argv[0], '<airline/retail>', "<Config File Path>"