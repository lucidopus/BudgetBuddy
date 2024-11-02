import os
import smtplib as smtp, time, requests, firebase_admin, confidential
from datetime import datetime
from firebase_admin import credentials, db
from bs4 import BeautifulSoup
from requests.models import MissingSchema

global actualPrice, customerPrice, link, pName, receiver

headers = {
    "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36'
    }

cred = credentials.Certificate('firebase-sdk.json')

firebase_admin.initialize_app(cred, {

    "databaseURL" : os.getenv("database-url")
})

ref = db.reference('/')

def send_email(title, link, receiver):
    server = smtp.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()

    receiver = receiver
    
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

try:
    while True:

        dictionary = ref.child("Requests").get()

        try:
            for key in dictionary:
                
                try:
                    actualPrice = ref.child("Requests").child(key).child("Actual Price").get()
                    customerPrice = ref.child("Requests").child(key).child("Customer Price").get()
                    link = ref.child("Requests").child(key).child("link").get()
                    pName = ref.child("Requests").child(key).child("Product Name").get()
                    receiver = ref.child("Requests").child(key).child("email").get()
                
                    page = requests.get(link, headers=headers)
                    soup = BeautifulSoup(page.content, 'html.parser')
                    price = soup.find(id = 'priceblock_ourprice').get_text()
                    price.strip()
                    c = price[1:len(price)-3]
                    price_integer = int(c.replace(',', ''))
                except MissingSchema and AttributeError:
                    pass

                if(price_integer <= customerPrice):
                    send_email(pName, link, receiver)
                    delete_entry(key)
                else:
                    print("Rechecking... "+ pName)
                    pass
            time.sleep(900)
        except TypeError:
            print("Sleeping")
            time.sleep(10)
            pass
except KeyboardInterrupt:

    today = datetime.now()
    interrupt = "The script stopped on "+str(today)
    print(interrupt)

except Exception as e:
    print(e)
