# Notion_Agent
A Notion Agent for Page/DB control and automatic send gmail.

## Main functions:
1. Support notion Page create, modify and update.
2. Avaliable for notion DB query (JSON).
3. Forward new post Pages (within 5 minutes) through Gmail automatically.

## Libraries and Depends:
### Google API CLI,  Oauthlib
```
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```
## Gmail Settings:
1. [Create and dwownlead credentials.json from OAuth, and save it to the same directory.](https://developers.google.com/gmail/api/quickstart/python)

2. [Get refresh token](https://developers.google.com/oauthplayground)

## Notion Settings:
1. [Create a notion integration.](https://developers.notion.com/docs/create-a-notion-integration)

2. Connect published pages with DB. 
