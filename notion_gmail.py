import os.path
import requests,json
import  datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from email.message import EmailMessage

import sys
sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")

# Gmail settings
refresh_token = ""
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
#Notion settings
token = ''
databaseID =""
headers = {
      "Authorization": "Bearer " + token,
      "Content-Type": "application/json",
      "Notion-Version": "2022-02-22"
}

class notionDBService():
  def __init__(self):
    self.pages = []
    self.minute = 5
    self.message =[]
    

  def responseDatabase(self):
    readUrl=f"https://api.notion.com/v1/databases/{databaseID}"
    res=requests.request("GET",readUrl,headers=headers)
    print(f'Status Code: {res.status_code}' )

  def readDatabase(self):
    readUrl = f"https://api.notion.com/v1/databases/{databaseID}/query"
    res = requests.request("POST", readUrl, headers=headers)
    data = res.json()
    print(res.status_code)
    # print(res.text)
    if res.status_code == 404:
      print(f'An error occurred: { data["message"]}')
      return []
    
    with open('./full-properties.json', 'w', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False)
    result = data['results']
    return result
  
  def readContent(pages,timeslot):
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=0)
    ts = datetime.datetime.timestamp(now)
    message = ''
    for p in pages:
      modifTime=p['last_edited_time']
      m = datetime.datetime.strptime(modifTime,'%Y-%m-%dT%H:%M:%S.%fZ')
      ts2=datetime.datetime.timestamp(m)
      if ((ts-ts2)<=timeslot*60 and (ts-ts2)>0):
        message+="\n"
        for key in p['properties']:
          if p['properties'][key]['type'] == 'rich_text':
            msg=p['properties'][key]['rich_text'][0]['plain_text']
          elif p['properties'][key]['type'] == 'title':
            msg=p['properties'][key]['title'][0]['plain_text']
          else:
            msg=' '
          message+= (key+' : ' + msg + "\n") #[0]['plain_text']
        message+= ('URL : '+ p['url'] + "\n")

    return message
    
  def getPageContet(self): #published 5 minutes ago
    self.pages = self.readDatabase()
    if len(self.pages) ==0:
      return ""
    message = self.readContent(self.pages,self.minute)
    return message


class notionPGService():
  def __init__(self,pageID: str = None,oldContent: str = None,newContent: str = None):
    self.pageID = pageID
    self.oldContent = oldContent
    self.newContent = newContent 

  def updatePG(self):
    updateUrl = f"https://api.notion.com/v1/pages/{self.pageID}" 
    
    response = requests.request("GET", updateUrl, headers=headers)
    if response.status_code == 200:
      Result = json.loads(response.text) 
      print('Page is obtained')
    updateContent = {"properties": Result["properties"]}

    # modify data
    updateContent = json.dumps(updateContent,ensure_ascii=False)
    # print(updateContent)
    def replaceContent(oldContent,newContent):
      update = updateContent.replace(oldContent,newContent)
      return update
    updateContent = replaceContent(self.oldContent,self.newContent)
    
    #update
    responseUp = requests.request("PATCH", updateUrl, headers=headers, data=updateContent.encode('utf-8')) #for chinese
        
    if responseUp.status_code == 200:
      print('Page is updated')
      print(responseUp.text)
    else:
      print('update error')
      print(responseUp.text)

  def createPG(self):
    createUrl = f"https://api.notion.com/v1/pages" 
    with open('newPage.json', 'r') as content_file:
      Result = content_file.read()

    responseCreate = requests.request("POST", createUrl, headers=headers, data=Result.encode('utf-8')) #for chinese
      
    if responseCreate.status_code == 200:
      print('Page is created')
      print(responseCreate.text)
    else:
      print('update error')
      print(responseCreate.text)
  
  def checkPGID(self):
    #get page ID
    noDB = notionDBService()
    result = noDB.readDatabase()
    
    #get title and pageID
    Content = {}
    for p in result:
      try:
        Content[p['properties']['商品名称']['title'][0]['plain_text']] = p['id'] 
      except:
        continue
    return Content
    

class emailService():
  def __init__(self,title,message,emailAddress,refresh_token: str=None,attachemnts: list=[]):
    self.title = title
    self.emailAddress = emailAddress
    self.message = message
    self.attachemnts = attachemnts
    self.refresh_token = refresh_token
    self.jsonfile = ''
    self.creds = None

  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
  def get_file(self):
    cwd = os.getcwd()
    onlyfiles = [os.path.join(cwd, f) for f in os.listdir(cwd) if os.path.isfile(os.path.join(cwd, f))]

    #multiple files check
    for i in onlyfiles:
      if i.find('.json') != -1 and len(self.jsonfile) == 0 and i.find('full-properties.json') == -1 and i.find('newPage.json') == -1:
        self.jsonfile=i

      elif i.find('.json') != -1 and i.find('full-properties.json') == -1 and i.find('newPage.json') == -1:
        print('Please keep only one valid credentials.json in this directory')


  def gerUserInfo(self):
    try:
      # Call the Gmail API
      service = build("gmail", "v1", credentials=self.creds)
      results = service.users().getProfile(userId="me").execute()
    except HttpError as error:
      print(f"An error occurred: {error}")

  def sendEmail(self):

    try:
      service = build("gmail", "v1", credentials=self.creds)
      message = EmailMessage()  
      message.set_content(self.Message)
      message['To'] = self.ClientEmail
      message['From'] = 'jie20ding@gmail.com'
      message['Subject'] = self.Title

      if self.attachments:
            for attachment in self.attachments:
                with open(attachment, 'rb') as content_file:
                    content = content_file.read()
                    message.add_attachment(content, maintype='application', subtype= (attachment.split('.')[1]), filename=attachment.split('/')[-1])


      # encoded message
      encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

      create_message = {
          'raw': encoded_message
      }
      email = service.users().messages().send(userId="me", 
                                              body=create_message).execute()
    except HttpError as error:
        print(f'An error occurred: {error}')

  def service1(self):
    self.get_file()
    
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    #add refresh token z
    with open(self.jsonfile, "r") as openfile:
      json_object = json.load(openfile)
    
    if json_object.get('refresh_token') == None:
      json_object["refresh_token"]  = self.refresh_token
      
    with open(self.jsonfile, "w") as outfile:
      json.dump(json_object, outfile)

    if len(self.jsonfile) != 0:
      creds = Credentials.from_authorized_user_file(
        filename = self.jsonfile,
        scopes=['https://mail.google.com/'],
        )
      # gerUserInfo()
      cwd = os.getcwd()
      #without attachment
      self.sendEmail(self.title,self.message,self.emailAddress)
      #with attachment
      # sendEmail(self.title,self.message,self.emailAddress,[os.path.join(cwd, 'try.pdf')])
    else:
      print('No credential detected. Please put your valid credentials.json in this directory')



if __name__ == "__main__":

  # noDB = notionDBService()
  # message = noDB.getPageContet()

  # if message != "":
  #   title = 'Medicine list update'
  #   emailAddress='jiefeiding@gmail.com'
  #   emS = emailService(title,emailAddress,message,refresh_token)
  #   emS.service1()
  PageID = 
  ContentOld=
  ContentNew=
  noPG = notionPGService(PageID,ContentOld,ContentNew)
  noPG.updatePG()
