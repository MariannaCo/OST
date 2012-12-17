from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users
from random import randint
from xml.dom import minidom
from xml.dom.minidom import Document
import cgi
import os

current_user=""

class User(db.Model):
        name = db.StringProperty()	

class Category(db.Model):
	name = db.StringProperty()
	user = db.StringProperty()  

class Item(db.Model):
	name = db.StringProperty()
	wins = db.IntegerProperty()

class Voted(webapp.RequestHandler): 
    def post(self):
        form = cgi.FieldStorage()
	category_name = form['category'].value
	category_user = form['category_user'].value
	global current_user
	uname = User(key_name=category_user)
           
	category_name = form['category'].value
	item_name = (form.getvalue('item')).strip(" ")
	item1 = (form.getvalue('item1')).strip(" ")
	item2 = (form.getvalue('item2')).strip(" ")
		
	item_k = db.Key.from_path('User', category_user,'Category',category_name,'Item',item_name)
	item_address = db.get(item_k)

	item_address.wins = item_address.wins + 1
	item_address.put()
	
	if item_name == item1:
		winnerWins =item_address.wins
		other_k = db.Key.from_path('User', category_user, 'Category',category_name,'Item',item2)
		other_address = db.get(other_k)
		otherWins =other_address.wins
		template_values = {
			'winner':item1,
			'otherItem':item2,
			'winnerWins':winnerWins,
			'otherWins':otherWins,
			'category_user':category_user,
			'category':category_name
		}
	else:   
		winnerWins =item_address.wins
		other_k = db.Key.from_path('User',category_user,'Category',category_name,'Item',item1)
		other_address = db.get(other_k)
		otherWins=other_address.wins
		template_values = {
			'winner':item2,
			'otherItem':item1,
			'winnerWins':winnerWins,
			'otherWins':otherWins,
			'category_user':category_user,
			'category':category_name
		}
	path = os.path.join(os.path.dirname(__file__), 'generate_table.html')
	self.response.out.write(template.render(path, template_values))

	category = Category(key_name=category_name, parent=uname)
	items = db.query_descendants(category)
	item1 = items[randint(0, items.count()-1)]
	if "item1" in form:
		prev_item1 = form['item1'].value
		while item1.name == prev_item1:
			item1 = items[randint(0, items.count()-1)]
	item2 = items[randint(0, items.count()-1)]
	while item1.name == item2.name:
		item2 = items[randint(0, items.count()-1)]
	template_values = { 
		'item1':item1.name,
		'item2':item2.name,
		'category':category_name,
		'category_user':category_user
	}
	path = os.path.join(os.path.dirname(__file__), 'vote_display_items.html')
	self.response.out.write(template.render(path, template_values))

class Search(webapp.RequestHandler):
    def post(self):
	    form = cgi.FieldStorage()
	    if 'category' not in form:
		self.response.out.write("<h3><i>No keyword was give. Please try again</i><h3>")
		self.response.out.write("<div>Go back to the <a href="'/'">welcome page</a><div>")
		return
	    keyword = (form['keyword'].value).strip(" ")
	    list = []
	    allUsers = db.GqlQuery("SELECT * "
				   "FROM User ")
	     
	    count = 0
	    for user in allUsers:
		    all = db.query_descendants(user)
		    for a in all:
			  if keyword in a.name:
				  list.append(a.name)
				  count = count + 1
				 # self.response.out.write("%s<br>" % a.name)
	    if count == 0:
		    self.response.out.write("<h3><i>Sorry nothing matched your search</i></h3>")
		    self.response.out.write("<div>Go back to the <a href="'/'">welcome page</a></div>")
		    return

	    self.response.out.write("<h3><i>The results for the keyword %s are:</i></h3><br>" % keyword)

	    for word in list:
	           self.response.out.write("%s<br>" % word)

	    self.response.out.write("<br><br><div>Go back to the <a href="'/'">welcome page</a><div>")
			                      
class Results(webapp.RequestHandler):
    def post(self):
    	global current_user
        form = cgi.FieldStorage()
	category_name = (form['category'].value).strip(" ")
	category_user = (form['category_user'].value).strip(" ")
	uname = User(key_name=category_user)
	category = Category(key_name=category_name, parent=uname)
        allItems = db.query_descendants(category)
	
	template_values = {
		   'category':category_name,
		   'allItems':allItems
        }

	path = os.path.join(os.path.dirname(__file__), 'results.html')
        self.response.out.write(template.render(path, template_values))

class Export(webapp.RequestHandler):
    def post(self):
    	global current_user
        form = cgi.FieldStorage()
	category_name = (form['category'].value).strip(" ")
	category_user = (form[category_name].value).strip(" ")
	uname = User(key_name=category_user)
	category = Category(key_name=category_name, parent=uname)
        allItems = db.query_descendants(category)
	
	doc = Document()
	#create category element
	cat = doc.createElement('CATEGORY')
	doc.appendChild(cat)
	#create name element
	name = doc.createElement('NAME')
	cat.appendChild(name)
	#create text node inside name
	n = doc.createTextNode(category_name)
	name.appendChild(n)
	

	for i in allItems:
		#create item element
		item = doc.createElement('ITEM')
		cat.appendChild(item)
		#create name element
		name = doc.createElement('NAME')
		item.appendChild(name)
		#create text node inside name
		n = doc.createTextNode(i.name)
		name.appendChild(n)

	self.response.out.write("%s" % doc.toprettyxml())
	self.response.out.write("<br><br><div>Go back to the <a href="'/'">welcome page</a><div>")

class UploadFile(webapp.RequestHandler):
    def post(self):
        global current_user
	uname=User(key_name=current_user.nickname())    
        form = cgi.FieldStorage()
	if 'datafile' not in form:
		self.response.out.write("<h3><i>Wrong input, please try again</i><h3>")
		self.response.out.write("<div>Go back to the <a href="'/'">welcome page</a><div>")
		return

	fileData = (form['datafile'].value).strip(" ")
	if not fileData:
		self.response.out.write("<h3><i>File was not found. Please try again</i><h3>")
		self.response.out.write("<div>Go back to the <a href="'/'">welcome page</a><div>")
		return

	data = minidom.parseString(fileData)
	elements = data.documentElement
	
	category_name_tag = elements.getElementsByTagName("NAME")[0].toxml()
	category_name=category_name_tag.replace('<NAME>','').replace('</NAME>','')
	category_name = category_name.strip(" ")
	category = Category(key_name=category_name, parent=uname)
	category.name=category_name
	category.user=current_user.nickname()
	category.put()

	cat = Category(key_name=category_name, parent=uname)

	itemsArray = []
	items = elements.getElementsByTagName("ITEM")
	for i in items:
		iTag = i.toxml() 
		name = iTag.replace('<ITEM>','').replace('</ITEM>','')
		name = name.replace('<NAME>','').replace('</NAME>','')
		name = name.replace('\n', '')
		name = name.strip(" ")
		item = Item(key_name=name, parent=cat)
		item.name=name
		item.wins=0
		item.put()
		itemsArray.append(name)

	template_values = {
		'category':category_name,
		'allItems': itemsArray
        }
	path = os.path.join(os.path.dirname(__file__), 'addCategoryXmlSucc.html')
	self.response.out.write(template.render(path, template_values))

class ChangeItemName(webapp.RequestHandler):
    def post(self):
	    global current_user
	    form = cgi.FieldStorage()
	    if 'item' not in form:
		self.response.out.write("<h3><i>Wrong input, please try again</i><h3>")
		self.response.out.write("<div>Go back to the <a href="'/'">welcome page</a><div>")
		return
	    new_name = (form['item'].value).strip(" ")
	    old_name = (form['oldItem'].value).strip(" ")
	    category = (form['category'].value).strip(" ")

	    c_key = db.Key.from_path('User', current_user.nickname(), 'Category', category_name)
	    catItems = db.GqlQuery("SELECT * "
				   "FROM Item "
				   "WHERE ANCESTOR IS :1 ",
				   c_key)

	    for i in catItems:
		    if i.name == new_name:
			    self.response.out.write("<h4><i>Category %s already has item %s</i></h4>" % (category_name,item_name))
			    self.response.out.write("<div>Go back to the <a href="'/'">welcome page</a><div>")
			    return


	    old_item_key = db.Key.from_path('User', current_user.nickname(), 'Category', category, 'Item', old_name) 
	    old_item = db.get(old_item_key)	       

	    uname = User(key_name=current_user.nickname())
	    cat = Category(key_name=category, parent=uname)

	    new_item = Item(key_name=new_name, parent=cat)
	    new_item.name=new_name
	    new_item.wins=old_item.wins
	    new_item.put()
	    
	    old_item.delete()
            self.response.out.write("<h4>You have changed the name of the item from <i>%s</i> to <i>%s</i></h4>" % (old_name,new_name))
	    self.response.out.write("<br><div>Go back to the <a href="'/'">welcome page</a></div>")

class ChangeName(webapp.RequestHandler):
    def post(self):
	    form = cgi.FieldStorage()
	    global current_user

	    if 'category' not in form:
		self.response.out.write("<h3><i>Wrong input, please try again</i><h3>")
		self.response.out.write("<div>Go back to the <a href="'/'">welcome page</a><div>")
		return

	    new_name = (form['category'].value).strip(" ")
	    old_name = (form['oldCat'].value).strip(" ")
	    category = (form['category'].value).strip(" ")
	    
	    user_key = db.Key.from_path('User', current_user.nickname())
	    userCategories = db.GqlQuery("SELECT * "
				     "FROM Category "
				     "WHERE ANCESTOR IS :1 ",
				      user_key)
	    for c in userCategories:
		if c.name == new_name:
			self.response.out.write("<h3><i>You already have a category with this name.</i></h3>")
			self.response.out.write("<div>Go back to the <a href="'/'">welcome page</a><div>")
			return

	    global current_user
	    uname = User(key_name=current_user.nickname())
	    #get old category and items
	    oldCat = Category(key_name=old_name, parent=uname)
	    items = db.query_descendants(oldCat)

	    uname=User(key_name=current_user.nickname())
	    #create new category with the new name
	    category = Category(key_name=new_name, parent=uname)
	    category.name=new_name
	    category.user = current_user.nickname()
	    category.put()

	    newCat = Category(key_name=new_name, parent=uname)
	    
	    for old_item in items:
		    new_item = Item(key_name=old_item.name, parent=newCat)
		    new_item.name=old_item.name
		    new_item.wins=old_item.wins
		    new_item.put()
		    

	    for old_item in items:
		    old_item.delete()
	    oldCat.delete()
	    self.response.out.write("<h4>You have changed the name of the category from <i>%s</i> to <i>%s</i></h4>" % (old_name,new_name))
	    self.response.out.write("<br><div>Go back to the <a href="'/'">welcome page</a></div>")
	    return

class EditItems(webapp.RequestHandler):
    def post(self):
         form = cgi.FieldStorage()
	 category_name = (form['category'].value).strip(" ")
	 action = (form['action'].value).strip(" ")
	 item = (form['item'].value).strip(" ")
	 global current_user

	 if action == "Delete":
		 if item == "No item":
			 self.response.out.write("The item you have selected is not valid")
			 self.response.out.write("<br><div>Go back to the <a href="'/'">welcome page</a><div>")
			 return

		 cat_key = db.Key.from_path('User', current_user.nickname(), 'Category', category_name)
		 catItems = db.GqlQuery("SELECT * "
		 		       "FROM Item "
		 		       "WHERE ANCESTOR IS :1 ",
		 			cat_key)
	         count = 0
		 for i in catItems:
			count = count + 1
		 if count == 2:
			 self.response.out.write("<h4><i>Sorry, this item cannot be deleted. A category must have at least two items</i></h4>")
			 self.response.out.write("<div>Go back to the <a href="'/'">welcome page</a><div>")
			 return

		 item_key = db.Key.from_path('User', current_user.nickname(), 'Category', category_name, 'Item', item) 
		 db.delete(item_key)
	         self.response.out.write("You have deleted item: %s" % item)
		 self.response.out.write("<br><br><div>Go back to the <a href="'/'">welcome page</a><div>")
		 return

	 elif action == "Change name":
		 if item == "No item":
			 self.response.out.write("The item you have selected is not valid")
			 self.response.out.write("<br><div>Go back to the <a href="'/'">welcome page</a><div>")
			 return
		 template_values = {
		       'category':category_name,
		       'item':item
	         }
	         path = os.path.join(os.path.dirname(__file__), 'changeItemName.html')

	 else:
	 	 template_values = {'category': category_name}
	 	 path = os.path.join(os.path.dirname(__file__), 'addItem.html')
	 	 
	 
	 self.response.out.write(template.render(path, template_values))
    	
class EditCategory(webapp.RequestHandler):
    def post(self):
         form = cgi.FieldStorage()
	 category_name = (form['category'].value).strip(" ")
	 action = (form['action'].value).strip(" ")
	 global current_user

	 uname = User(key_name=current_user.nickname())
	 category = Category(key_name=category_name, parent=uname)
	 items = db.query_descendants(category)

	 if action == "Edit Items":
                 template_values = {
		       'category':category_name,
		       'allItems':items
	         }
	         path = os.path.join(os.path.dirname(__file__), 'editItems.html')
	 
	 elif action == "Change name":
		 template_values = {
		       'category':category_name,
	         }
	         path = os.path.join(os.path.dirname(__file__), 'changeCatName.html')
	 else:
		 for item in items:
			 item.delete()
		 category.delete()

		 self.response.out.write("You have deleted category: %s" % category_name)
		 self.response.out.write("<br><br><div>Go back to the <a href="'/'">welcome page</a><div>")
		 return

	 self.response.out.write(template.render(path, template_values))

class CreateItem(webapp.RequestHandler):
    def post(self):
        form = cgi.FieldStorage()
	if 'item' not in form:
		self.response.out.write("<h3><i>Wrong input, please try again</i><h3>")
		self.response.out.write("<div>Go back to the <a href="'/'">welcome page</a><div>")
		return

	category_name = (form['category'].value).strip(" ")
        item_name = (form['item'].value).strip(" ")

	cat_key = db.Key.from_path('User', current_user.nickname(), 'Category', category_name)
	catItems = db.GqlQuery("SELECT * "
			       "FROM Item "
			       "WHERE ANCESTOR IS :1 ",
			       cat_key)

	for i in catItems:
		if i.name == item_name:
			self.response.out.write("<h3><i>Category %s already has item %s</i></h3>" % (category_name,item_name))
			self.response.out.write("<div>Go back to the <a href="'/'">welcome page</a><div>")
			return


	global current_user
	uname=User(key_name=current_user.nickname())
	cat = Category(key_name=category_name, parent=uname)

	item = Item(key_name=item_name, parent=cat)
	item.name=item_name
	item.wins=0
	item.put()
	
	self.response.out.write("You have added item %s to category %s" % (item_name,category_name))
	self.response.out.write("<br><br><div>Go back to the <a href="'/'">welcome page</a><div>")

class CreateCategory(webapp.RequestHandler):
    def post(self):
        form = cgi.FieldStorage()
	if 'category' not in form or 'item1' not in form or 'item2' not in form:
		self.response.out.write("<h3><i>Wrong input, please try again</i><h3>")
		self.response.out.write("<div>Go back to the <a href="'/'">welcome page</a><div>")
		return

	category_name = (form['category'].value).strip(" ")
        item1_name = (form['item1'].value).strip(" ")
	item2_name = (form['item2'].value).strip(" ")
	global current_user

	user_key = db.Key.from_path('User', current_user.nickname())
	userCategories = db.GqlQuery("SELECT * "
				     "FROM Category "
				     "WHERE ANCESTOR IS :1 ",
				      user_key)
	for c in userCategories:
		if c.name == category_name:
			self.response.out.write("<h3><i>You already have a category with this name.</i></h3>")
			self.response.out.write("<div>Go back to the <a href="'/'">welcome page</a><div>")
			return

	uname=User(key_name=current_user.nickname())

	category = Category(key_name=category_name, parent=uname)
	category.name=category_name
	category.user=current_user.nickname()
	category.put()
	
	cat = Category(key_name=category_name, parent=uname)

	item1 = Item(key_name=item1_name, parent=cat)
	item1.name=item1_name
	item1.wins=0
	item1.put()

	item2 = Item(key_name=item2_name, parent=cat)
	item2.name=item2_name
	item2.wins=0
	item2.put()

	template_values = {
		'category':category_name,
		'item1':item1_name,
		'item2':item2_name
        }
	path = os.path.join(os.path.dirname(__file__), 'addCategorySuccess.html')
        self.response.out.write(template.render(path, template_values))

class AddMoreItems(webapp.RequestHandler):
    def post(self):
        form = cgi.FieldStorage()
        global current_user
	category_name = (form['category'].value).strip(" ")
	click = (form['click'].value).strip(" ")
	uname = User(key_name=current_user.nickname())
	cat = Category(key_name=category_name, parent=uname)
        
	if "item" in form:
		item_name = (form['item'].value).strip(" ")

		cat_key = db.Key.from_path('User', current_user.nickname(), 'Category', category_name)
		catItems = db.GqlQuery("SELECT * "
				       "FROM Item "
				       "WHERE ANCESTOR IS :1 ",
				       cat_key)

		for i in catItems:
			if i.name == item_name:
				self.response.out.write("<h4><i>Category %s already has item %s</i></h4>" % (category_name,item_name))
				self.response.out.write("<div>Go back to the <a href="'/'">welcome page</a><div>")
				return

		
		item = Item(key_name=item_name, parent=cat)
		item.name=item_name
		item.wins=0
		item.put()
	else:
		if "addPage" in form:
			self.response.out.write("<h3><i>Wrong input, please try again</i><h3>")
			self.response.out.write("<div>Go back to the <a href="'/'">welcome page</a><div>")
			return

	
	submit_click = (form['click'].value).strip("")
	if submit_click == "Yes":
		template_values = {'category':category_name}
		path = os.path.join(os.path.dirname(__file__), 'addMoreItems.html')
	else:
                template_values = {}
                path = os.path.join(os.path.dirname(__file__), 'welcome.html')
        
	self.response.out.write(template.render(path, template_values))
		

		
class DisplayItems(webapp.RequestHandler):
    def post(self):
	form = cgi.FieldStorage()
	category_name = form['category'].value
	if category_name in form:
		category_user = form[category_name].value
	else:
		category_user = form["category_user"].value
	global current_user
	uname = User(key_name=category_user)
	category = Category(key_name=category_name, parent=uname)
        
	items = db.query_descendants(category)
	item1 = items[randint(0, items.count()-1)]
	if "item1" in form:
		prev_item1 = form['item1'].value
		while item1.name == prev_item1:
			item1 = items[randint(0, items.count()-1)]
	item2 = items[randint(0, items.count()-1)]
	while item1.name == item2.name:
		item2 = items[randint(0, items.count()-1)]
	template_values = { 
		'item1':item1.name,
		'item2':item2.name,
		'category':category_name,
		'category_user':category_user
	}
	path = os.path.join(os.path.dirname(__file__), 'vote_display_items.html')
	self.response.out.write(template.render(path, template_values))

class ChooseAction(webapp.RequestHandler):
    def post(self):
        global current_user
        form = cgi.FieldStorage()
	action = form['action'].value
	if action == "Vote":
	   allCategories = db.GqlQuery("SELECT * "
				       "FROM Category ")
	   count=0
	   for cat in allCategories:
		   count = count + 1
	   if count == 0:
                 self.response.out.write("<h3><i>Sorry, there are curently no categories to vote for.</h3></i>")
		 self.response.out.write("<div>Go back to the <a href="'/'">welcome page</a><div>")
		 return

	   template_values = {
		   'user':current_user.nickname(),
		   'allCategories':allCategories
           }
	   path = os.path.join(os.path.dirname(__file__), 'vote_display_categories.html')

	elif action == "Add a category":
           template_values = {}
	   path = os.path.join(os.path.dirname(__file__), 'addCategory.html')

        elif action =="Edit a category":
           user_key = db.Key.from_path('User', current_user.nickname())
	   userCategories = db.GqlQuery("SELECT * "
					"FROM Category "
					"WHERE ANCESTOR IS :1 ",
					 user_key)
	   count=0
	   for cat in userCategories:
		   count = count + 1
	   if count == 0:
                 self.response.out.write("<h3><i>Sorry, you do not have any categories.</h3></i>")
		 self.response.out.write("<div>Go back to the <a href="'/'">welcome page</a><div>")
		 return
	   template_values = {
		    'userCategories':userCategories
	   }	
	   path = os.path.join(os.path.dirname(__file__), 'editCategory.html')

	elif action == "Export":
           allCategories = db.GqlQuery("SELECT * "
				       "FROM Category ")
	   count=0
	   for cat in allCategories:
		   count = count + 1
	   if count == 0:
                 self.response.out.write("<h3><i>Sorry, there are curently no categories to export.</h3></i>")
		 self.response.out.write("<div>Go back to the <a href="'/'">welcome page</a><div>")
		 return

	   template_values = {
		   'allCategories':allCategories
           }
	   path = os.path.join(os.path.dirname(__file__), 'export_display_categories.html')
	elif action == "Search":
	    template_values = {}
	    path = os.path.join(os.path.dirname(__file__), 'search.html')
	else:
	   template_values = {}
	   path = os.path.join(os.path.dirname(__file__), 'uploadXmlFile.html')	      

        self.response.out.write(template.render(path, template_values))
 
class MainPage(webapp.RequestHandler):
    def get(self):
	global current_user
	current_user = users.get_current_user()
    
	if current_user:
	   allUsers = db.GqlQuery("SELECT * "
	   			  "FROM User ")
	   user_exists = 0
	   for user in allUsers:
	       if current_user.nickname() == user.name:
	   	  user_exists = 1
	   	  break
	   
	   if  user_exists == 0:
	       new_user = User(key_name=current_user.nickname())
	       new_user.name = current_user.nickname()
	       new_user.put()
	    
	   template_values = {
	          'user':current_user.nickname()
	   }	
	   path = os.path.join(os.path.dirname(__file__), 'welcome.html')
	   self.response.out.write(template.render(path, template_values))
	else:
          self.redirect(users.create_login_url(self.request.uri))
	  

application = webapp.WSGIApplication(
                                     [('/', MainPage),
				      ('/items', DisplayItems),
				      ('/createCategory', CreateCategory),
				      ('/chooseAction', ChooseAction),
				      ('/voted', Voted),
				      ('/addMoreItems', AddMoreItems),
				      ('/results', Results),
				      ('/uploadFile',UploadFile),
				      ('/export', Export),
				      ('/edit',EditCategory),
				      ('/changeName', ChangeName),
				      ('/editItems', EditItems),
				      ('/changeItemName', ChangeItemName),
				      ('/createItem', CreateItem),
				      ('/search', Search)],
                                     debug=True)
    

def main():
    run_wsgi_app(application)


if __name__ == "__main__":
    main()


