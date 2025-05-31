from bs4 import BeautifulSoup
from fake_useragent import UserAgent
ua = UserAgent()
import requests
import pandas as pd
import re
import html2text

def get_headers():  
    headers = {'User-Agent': ua.random}
    return headers

link = 'https://habr.com/ru/articles/432466/' 

page = requests.get(link, headers = get_headers())
soup = BeautifulSoup(page.text,'lxml')

text_doc = pd.DataFrame(columns = ['link', 'name','text']) 
a = soup.find_all('li')    
for i in a:                  
    if re.search(r'consultant', str(i)) == None:  
        continue
    link = re.search(r'href=\S*',str(i)) 
    link = re.sub(r'href=','',link[0]) 
    number_doc = re.search(r'\d{4,7}',link)  
    name = re.search(r'noreferrer">.*\s*(?:<\/a|<\/a>\s)', str(i))   
    name = re.sub(r'(?:noreferrer">|<\/a|<\/a>\s|\[.*\s*|>)', '', str(name[0]))
    url = f'https://www.consultant.ru/cons/cgi/online.cgi?req=doc&base=LAW&n={number_doc[0]}&dst=100001&docaccess=ALWAYS&current=0&content=text&rnd=LFOSRgUmOqJArPeZ2&_=1742797600120&rnd=LFOSRgUmOqJArPeZ2'
    a = requests.get(url, headers = get_headers())
    asd = BeautifulSoup(a.text,'html.parser') 
    text_maker = html2text.HTML2Text() 
    text_maker.ignore_links = True
    das = text_maker.handle(str(asd))
    text = re.sub(r'(?:{"sett.*content":"|{"from.*content":"|\/|\\|}|{|\n|[a-z])', '', str(das)) 
    
    doc_item = {'link':link, 'name':name,'text':text} 
    text_doc = text_doc.append(doc_item, ignore_index = True) 
text_zak.to_excel('consultant_zakon2.xlsx', index = False) 