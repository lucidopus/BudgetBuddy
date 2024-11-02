import os
import requests, time, random, uuid, firebase_admin, confidential, subprocess
from requests.models import MissingSchema
import smtplib as smtp
from firebase_admin import credentials, db
from bs4 import BeautifulSoup 


cred = credentials.Certificate('firebase-sdk.json')

firebase_admin.initialize_app(cred, {

    "databaseURL" : os.getenv("database-url")
})

ref = db.reference('/')

filename = "requests.json"

wait = [
    'I\'ll notify you via email when the prices are dropped!',
    'You\'ll be notified',
    'Okay, noted!'    
    ]

class EmailError(Exception):

    def __init__(self, message="Please enter a valid email!"):
        self.message = message
        super().__init__(self.message)

class RequestAlreadyExistsError(Exception):

    def __init__(self,message="Request already exists!"):
        self.message = message
        super().__init__(self.message)


def run_notify():
    cmd = "python notify.py"
    p = subprocess.Popen(cmd, shell=True)
    out, err = p.communicate()

def acknowledge():

    global email

    try:
        customer_required_price = int(input("At what price would you like to get notified?: "))

        email = str(input("Enter the email at which you want to send the email at: "))
        if not ('@' and ('.com' or '.in') in email):
            raise EmailError
        pass  

    except ValueError:
        print("Make sure that the price is an integer!")
        
    price = soup.find(id = 'priceblock_ourprice').get_text()
    price.strip()
    c = price[1:len(price)-3]
    price_integer = int(c.replace(',', ''))

    if(price_integer <= customer_required_price):
        print("The prices are already low!")
    else:

        name = soup.find(id = 'title').get_text()
        name = name[9:(len(name)-8)]   #Product title
        
        checkForMultipleRequests(name, price_integer, customer_required_price, link, email)
        push(name, price_integer, customer_required_price, link, email)
        print(wait[random.randrange(3)])

def link_check(link):
    flag = 1
    while(flag==1):
        try:
            page = requests.get(link, headers=headers)
            soup = BeautifulSoup(page.content, 'html.parser')
            soup.find(id = 'title').get_text()
            flag = 0

        except AttributeError as e:
            print("Please enter a valid amazon product link!" +str(e))
            link = str(input("Paste the amazon product link here: "))
            link_check(link) 

def get_product_details():

    global price_integer, title, price

    try:
        title = soup.find(id = 'title').get_text()   #Product title
        print(title.strip()+'\n')
        ratings_raw = soup.find(class_ = 'a-icon-alt').get_text()  #Product ratings
        print("Product Ratings: "+ratings_raw.strip())

        strike_mrp = soup.find(class_ = 'priceBlockStrikePriceString a-text-strike').get_text()    #striked rate (IF ANY)
        print("Original Price: "+strike_mrp.strip())

        savings = soup.find(id = 'regularprice_savings').get_text()    #savings (IF ANY)
        savings.strip()
        a = str(savings[15:])
        print("Savings: "+a[:16])

        price = soup.find(id = 'priceblock_ourprice').get_text()   #current price
        print("Amazon Price: "+price.strip())

        c = price[1:len(price)-3]
        price_integer = int(c.replace(',', ''))

    except AttributeError:

        try:
            price = soup.find(id = 'priceblock_ourprice').get_text()   #current price
            print("Amazon Price: "+price.strip())
            print("There are currently no discounts on this product!")
        except AttributeError:
            print("Item is unavailable!")
            return "Item is unavailable!"                        
        pass

def push(title, price, customer_price, link, email):
    ref = db.reference("Requests")

    ref.push({
        
            "Product Name" : title,
            "Actual Price" : price,
            "Customer Price" : customer_price,
            "link" : link,
            "email" : email
    })

def checkForMultipleRequests(title, price, customer_price, link, email):

    dictionary = ref.child("Requests").get()

    try:

        for i in dictionary : 

            ap = ref.child("Requests").child(i).child("Actual Price").get()
            cp = ref.child("Requests").child(i).child("Customer Price").get()
            pn = ref.child("Requests").child(i).child("Product Name").get()
            l = ref.child("Requests").child(i).child("link").get()
            e = ref.child("Requests").child(i).child("email").get()

            if(title == pn):
                if(price == ap):
                    if(customer_price == cp):
                        if(link == l):
                            if(email == e):
                                raise RequestAlreadyExistsError
                            pass
                        pass
                    pass
                pass
            pass
    except TypeError:
        pass

def send_email(title, link):
    server = smtp.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()

    receiver = 'harshilpatel30401@gmail.com'

    # username = credentials.username_kitt
    # password = credentials.password_kitt

    username = confidential.username_kitt  
    password = confidential.password_kitt

    server.login(username, password)
    subject = "The prices are down!"
    # body = f"\n\n\n\n\n\n\n\n\n{title}\n\n\n\n\n\n\n\n {link}"
    body = f"{title} \n\n Product Link:\n{link}"
    composed_message = f"Subject: {subject}\n\n {body}"

    server.sendmail(
        from_addr=username,
        to_addrs=receiver,
        msg=composed_message.encode('utf-8').strip()
    )

    # print("EMAIL SENT")
    server.quit()

def delete_entry(userId):
    ref.child("Requests").child(userId).delete()

def notify():
    
    dictionary = ref.child("Requests").get()

    try:
        for key in dictionary:
            
            try:
                actualPrice = ref.child("Requests").child(key).child("Actual Price").get()
                customerPrice = ref.child("Requests").child(key).child("Customer Price").get()
                link = ref.child("Requests").child(key).child("link").get()
                pName = ref.child("Requests").child(key).child("Product Name").get()
            
                page = requests.get(link, headers=headers)
                soup = BeautifulSoup(page.content, 'html.parser')
                price = soup.find(id = 'priceblock_ourprice').get_text()
                price.strip()
                c = price[1:len(price)-3]
                price_integer = int(c.replace(',', ''))
            except MissingSchema and AttributeError:
                pass

            if(price_integer <= customerPrice):
                send_email(pName, link)
                delete_entry(key)
            else:
                print("Rechecking... "+ pName)
        time.sleep(900)
    except TypeError:
        print("Sleeping")
        time.sleep(10)

headers = {
    "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36'
    }

try:
    while 1:

        uid = str(uuid.uuid4())

        # starter()

        print("\n")
        link = str(input("Paste the amazon product link here: "))
        print("\n")

        link_check(link)

        page = requests.get(link, headers=headers)

        soup = BeautifulSoup(page.content, 'html.parser')

        if (get_product_details() == "Item is unavailable!"):
            continue
        # else:
            # get_product_details()
        try:

            acknowledge()  

        except UnboundLocalError:
            continue

        except EmailError:
            print("Enter a valid email address!")
            continue

        except RequestAlreadyExistsError:
            print("This request has already been registered, you will be notified when your requirements have been met.")
            continue


except KeyboardInterrupt:
    print("Bye")
