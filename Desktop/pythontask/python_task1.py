import cookielib, urllib2, sys
import requests
from bs4 import BeautifulSoup
import urllib
import zipfile
import datetime
import os 

import re
import cherrypy
from os.path import abspath
from jinja2 import Environment, FileSystemLoader
import csv
import redis
env = Environment(loader=FileSystemLoader('templates'))
data_base=11
r = redis.Redis(host='localhost', port=6379, db=0)


def get_data():  
    #UEL Link to extract data
    url='https://www.bseindia.com/markets/equity/EQReports/Equitydebcopy.aspx'
    
    #open with GET method
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}
    
    r = requests.get(url, headers=headers, timeout=5)
    #http_respone 200 means OK status
    if r.status_code==200:
        print("Successfully opened the web page")
    soup1=BeautifulSoup(r.text,'html.parser')
    count=0
     # print the date object, not the container ;-)
    
    for a1 in soup1.findAll("a"):
    
        if ".ZIP" in a1['href'] or ".zip" in a1['href'] :
            
            download_URL = str(a1['href'])
            #dwnlaod csv file
            download = requests.get(download_URL)
            
            f = urllib2.urlopen(download_URL)
            name="code"+str(count)+".zip"
            print name
            with open(name, "wb") as code:
                code.write(f.read())
                
            dir_path = os.path.dirname(os.path.realpath(__file__))

            path_to_zip_file=str(dir_path)+"/"+str(name)
            directory_to_extract_to="path/"
            #unzip the files
            zip_ref = zipfile.ZipFile(path_to_zip_file, 'r')
            zip_ref.extractall(directory_to_extract_to)
            zip_ref.close()
        count=count+1
    return "done"



def redis_load():
    get_data()
    mylist = []
    now = datetime.datetime.now()
    if len(str((now.month)))==1:
       
        string=str("18")+str("0")+str(now.month)+str("18")
    else:
        
        string=str("18")+str(now.month)+str("18")
   
    
    with open("path/EQ"+string+".CSV",'rt') as csvfile:
        #connect to redis database
        r = redis.Redis(host='localhost', port=6379, db=data_base) 
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        count=0
        for row in spamreader:
            #load csv data to redis
            r.set(count,row)
            count=count+1
            return "done"




def app():
    
    final_data=[]
    req=[]
    req1=[]
    redis_load()
    #get top 10 entries from redis database
    for i in range(1,11):
        
        final_data=r.get(i)
        final_data.strip()
        final_data=re.sub('[^a-zA-Z0-9 \n\.]', ' ',final_data)
        final_data= filter(None, final_data.split("   "))
        req.append(final_data)
    
    #get headers of the csv file    
    final_data1=r.get(0)
    final_data1.strip()
    final_data1=re.sub('[^a-zA-Z0-9 \n\.]', ' ',final_data1)
    final_data1= filter(None, final_data1.split("   "))
    req1.append(final_data1)
    tmpl = env.get_template('final_html.html')

    return tmpl.render(data1=req1,data=req)

app.exposed = True

CP_CONF = {
        '/media': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': abspath('./media') # staticdir needs an absolute path
            }
        }


if __name__ == '__main__':
    cherrypy.config.update({'server.socket_port': 8082})
    cherrypy.quickstart(app, '/', CP_CONF)
    