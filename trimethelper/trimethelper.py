from flask import Flask
from flask.ext.mail import Mail
from datetime import datetime
from flask_mail import Message
from crossdomain import crossdomain
import urllib, time, pytz
import urllib2, base64
import credentials, json
import os.path


TWITTER_APIKEY=credentials.twitterapikey
TWITTER_APISECRET=credentials.twitterapisecret
TWITTER_BEARERTOKEN=credentials.twitterbearertoken

TRIMET_APPID=credentials.trimetappid

MAIL_SERVER = credentials.MAIL_SERVER
MAIL_PORT = credentials.MAIL_PORT
MAIL_USE_TLS = credentials.MAIL_USE_TLS
MAIL_USE_SSL =  credentials.MAIL_USE_SSL
MAIL_USERNAME = credentials.MAIL_USERNAME
MAIL_PASSWORD = credentials.MAIL_PASSWORD

app = Flask(__name__)
app.config.from_object(__name__)
mail = Mail(app)


@app.route('/')
def hello():
    return "This server is a service. Please use the right path"


# functions for /getdashboard
@app.route('/getdashboard')
@crossdomain(origin='*')
def getdashboard():
    locationids = '1003,1114,9978,10168'
    url = 'http://developer.trimet.org/ws/v2/arrivals?locIDs=' + locationids + '&json=true&appID=' + TRIMET_APPID
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    data = response.read()
    arrivals = json.loads(data)['resultSet']['arrival']
    filtered = filterdashboarddata(arrivals)
    dashboard = "{ 'arrivals':"+ json.dumps(filtered) +"}"
    return dashboard

def filterdashboarddata(arrivals):
    filtered = dict()
    for arrival in arrivals:
        locid = arrival['locid']        
        if(not filtered.has_key(locid)):
            filtered[locid] = list()
        filtered[locid].append(arrival)
    return filtered



# functions for /checktrimetstatus
#https://dev.twitter.com/docs/auth/application-only-auth
@app.route("/checktrimetstatus")
def checktrimetstatus():
    bearerToken = getBearerToken()
    authorization = 'Bearer ' + bearerToken
    headers = {'Authorization':authorization}
    url = 'https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=trimet'

    req = urllib2.Request(url, None, headers)
    response = urllib2.urlopen(req)
    data = response.read()   
    problems =  checkForProblems(data)
    problemsStr = str('<br/>'.join(problems))
    sendEmail(problemsStr)
    return problemsStr


def checkForProblems(data):
    tweetsJSON = json.loads(data)
    problems = []
    delayFound = False;
    for tweet in tweetsJSON:
        text = tweet['text']
        created_at_utc  = pytz.utc.localize(datetime.strptime(tweet['created_at'].replace('+0000 ',''), '%a %b %d %H:%M:%S %Y'))
        created_at = created_at_utc.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Pacific'))
        now = datetime.now(pytz.timezone('US/Pacific'))
        diff_seconds = (now - created_at).seconds
        # difference is less than 3 hours
        if(diff_seconds < 10800):
            if(text.find('delay') != -1 or text.find('close') != -1):
                problems.append('At : ' + str(created_at.hour) + ':' + str(created_at.minute) +  ', ' + text)
    return problems;


def sendEmail(problemsStr):
    fname = 'problems.txt'
    sendMail = False
    if(not os.path.isfile(fname)):
        sendMail = True
        with open(fname, 'w') as f:
            f.write(problemsStr)
        f.closed
    else:
        with open(fname,'r+') as f:
            existingproblems = f.read()
            if(existingproblems != problems):
                sendMail = True
                f.write(problemsStr)
        f.closed
    if(sendMail):
        msg = Message("Trimet problems",
                  sender=MAIL_USERNAME,
                  recipients=["athreya86@gmail.com"])
        msg.html = problemsStr
        mail.send(msg)

def getBearerToken():
    return TWITTER_BEARERTOKEN


# bearer tokens don't change for now - but they may change in the future
def getBearerTokenFromTwitter():
    # construct header first
    basic = base64.b64encode(urllib.quote_plus(TWITTER_APIKEY) + ':' + urllib.quote_plus(TWITTER_APISECRET))
    authorization = 'Basic ' + basic
    contentType = 'application/x-www-form-urlencoded;charset=UTF-8'
    headers = {'Authorization':authorization, 'Content-Type':contentType}
    # body then and make request
    body = 'grant_type=client_credentials'
    url = 'https://api.twitter.com/oauth2/token'
    req = urllib2.Request(url, body, headers)
    response = urllib2.urlopen(req)
    tokenJSON = json.loads(response.read())
    return tokenJSON['access_token']




if __name__ == "__main__":
    app.run(debug=True)
