import webapp2
from time import time
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import urllib2
import random
import string
import time

class Url(ndb.Model):
  u = ndb.StringProperty(indexed=True) # URL
  i = ndb.StringProperty(indexed=True) # id
  k = ndb.StringProperty(indexed=True) # key
  e = ndb.StringProperty(default="")  # email
  b = ndb.StringProperty(default="")  # bitcoin
  h = ndb.IntegerProperty(default=0) # hits

  ctime = ndb.DateTimeProperty(auto_now_add=True)
  mtime = ndb.DateTimeProperty(auto_now=True)

class MainPage(webapp2.RequestHandler):
  def get(self):

    if self.request.get('k'):
      # get the management key
      key = self.request.get('k')

      q = Url.query(Url.k == key)
      count = q.count()
      results=q.fetch(1)

      if count is 0:
        # bad key, bail out
        self.response.out.write("<html><body><br><br><center>error: unknown key")
        return

      for result in results:
        # spit out the config page       
        self.response.out.write('''
<html><head><center>
<form name="input" action="/" method="post">
<input type="hidden" name="key" value="'''+result.k+'''"><br>
id: kik.to/<input type="text" name="id" value="'''+result.i+'''"><br>
url: <input type="text" name="url" value="'''+result.u+'''"><br>
email: <input type="text" name="email" value="'''+result.e+'''"><br>
btc: <input type="text" name="btc" value="'''+result.b+'''"><br>

<input type="submit" value="update preferences">
</form><br>
total hits: '''+str(result.h))
      return

    # serve up the main landing page
    else:
      self.response.out.write('''
<html><head><title>kik.to</title></head>
<body><center><br><br>

<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>

<link rel="stylesheet" href="https://bootswatch.com/slate/bootstrap.min.css" crossorigin="anonymous">

<div class="container" style="width: 300px; margins: 0 auto;">
<form action="http://kik.to" method="post">
<div class="form-group" style="max-width: 300px;margins:0 auto;">
<label for="url">Kik.to Url Shortner:</label>
<input type="text" name="u" class="form-control" id="u" aria-describedby="urlHelp" placeholder="http://">
<small id="urlHelp" class="form-text text-muted">We'll never share your url with anyone else.</small>
</div>
<button type="submit" class="btn btn-primary">Submit</button>
</form>
</div>


<!--

<form name="input" action="/" method="post">
url:
<input type="text" name="u" value="http://">
<input type="submit" value="submit">
</form>
-->

''')

  def post(self):
    # we're updating a URL entry
    key = self.request.get('key')
    if key:
      q = Url.query(Url.k == key)
      if q.count() is 0:
        self.response.out.write('invalid key')
        return

      url = self.request.get('url')
      email = self.request.get('email')
      i = self.request.get('id')
      btc = self.request.get('btc')
    
      results=q.fetch(1)
      for result in results:

        # are we updating the ID?
        if result.i != i:
          # make sure the new ID they want isn't already taken
          q2 = Url.query(Url.i == i)
          if q2.count() > 0:
            self.response.out.write('''<html><body><br><br><center>sorry, that id is already taken''')
            return
          result.i=i # okay it checks out, update ID

        # update the the object and put it back in the database
        result.u=url
        result.e=email
        result.b=btc
        result.put()
        self.response.out.write('''<html><body><br><br><center>update successful<br><br>'''+url+" "+i+" "+email)
        return

    # okay, we're creating a new URL entry
    url=self.request.get('u')

    if url:
     for length in range(1,10):
      for attempt in range(1,5):
         newid = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(length))
         #newid = ''.join(random.choice(string.digits) for _ in range(length))

         # see if we've generated this ID before
         q = Url.query(Url.i == newid)
         if q.count() > 0:
           continue

         # 60 bits of entropy log62(2^60)~=10.7487
         newkey = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(10))

         newurl = Url(u=url, i=newid, k=newkey)
         newurl.put()
         self.response.out.write("<html><body><br><br><center>use kik.to/"+str(newid)+"<br><br>To edit later, bookmark <br>kik.to/?k="+newkey)
    #self.redirect("http://"+str(results.u))
         return
    return

class Bounce(webapp2.RequestHandler):
  def get(self):
    path=self.request.path.split('/')[1]
    #self.response.out.write("got "+str(path))

    q = Url.query(Url.i == path)
    count = q.count()
    results=q.fetch(1)

    if count is 0:
      self.response.out.write("nope")
      return

    # increase hit count
    for result in results:
      result.h+=1
      result.put()
      self.response.out.write('''
<br><br>
<center>
<b>Thank you for using kik.to!</b><br><br>
Taking you to <a href="'''+result.u+'''+">'''+result.u+'''</a><br><br>
total hits: '''+str(result.h)+'''
</center>
<script>
setTimeout(function()
{
  window.location="'''+result.u+'''"
},3000);
</script>''')

app = webapp2.WSGIApplication([('/',MainPage),('/.*',Bounce)])
