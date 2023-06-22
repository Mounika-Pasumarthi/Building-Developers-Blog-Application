from flask import Flask,redirect,render_template,url_for,request,flash,session
import mysql.connector
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from random import randint
import random
import string
from flask_session import Session
from key import secret_key,salt
from itsdangerous import URLSafeTimedSerializer
from stoken import token
from mailc import sendmail
app=Flask(__name__)
app.secret_key=secret_key
app.config['SESSION_TYPE']='filesystem'
mydb=mysql.connector.connect(host="localhost",user="root",password="admin",db="blog")
@app.route('/')
def index():
    return render_template('title.html')
#registration
@app.route('/registration',methods=['GET','POST'])
def registration():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        email=request.form['email']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*)  from users where username=%s',[username])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*)  from users where email=%s',[email])
        count1=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            flash('username is already in use')
            return render_template('registration.html')
        elif count1==1:
            flash('Email already in use')
            return render_template('registration.html')
        data={'username':username,'password':password,'email':email}
        subject='Email Confirmation'
        body=f"Thanks for signing up\n\n follow this link  further steps-{url_for('confirm',token=token(data),_external=True)}"
        sendmail(to=email,subject=subject,body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('login'))
    return render_template('registration.html')
#login
@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('home'))
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where username=%s and password=%s',[username,password])
        count=cursor.fetchone()[0]
        if count==1:
            session['user']=username
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
            return render_template('login.html')
    return render_template('login.html')
#forgot password
@app.route('/forgotpassword', methods=['GET','POST'])
def forgotpassword():
    if request.method=='POST':
            email=request.form['email']
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            cursor=mydb.cursor(buffered=True)
            cursor.execute("UPDATE users SET password = %s WHERE email = %s", (password, email))
            cursor.close()
            data={'password':password,'email':email}
            subject='Reset Password Confirmation'
            body = "Your new password is: " + password
            sendmail(to=email,subject=subject,body=body)
            flash('New password sent to mail')
            return redirect(url_for('login'))
            return render_template('registration.html')
    return render_template('forgot.html')
#homepage
@app.route('/homepage')
def home():
    if session.get('user'):
        return render_template('homepage.html')
    else:
        return redirect(url_for('login'))
#confirmation token generation
@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt,max_age=180)
    except Exception as e:
        #print(e)
        return 'Link Expired register again'
    else:
        cursor=mydb.cursor(buffered=True)
        username=data['username']
        cursor.execute('select count(*) from users where username=%s',[username])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.close()
            flash('you already registered')
            return redirect(url_for('login'))
        else:
            cursor.execute('insert into users values(%s,%s,%s)',[data['username'],data['password'],data['email']])
            mydb.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('login'))
#logout
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        flash('Successfully loged out')
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
#add post
@app.route('/addpost',methods=['GET','POST'])
def addpost():
    if session.get('user'):
        if request.method=='POST':
            title=request.form['title']
            content=request.form['content']
            username=session.get('user')
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into posts (title,content,added_by) values(%s,%s,%s)',[title,content,username])
            mydb.commit()
            cursor.close()
            flash('Post added successfully')
            return redirect(url_for('allpost'))
        return render_template('addpost.html')
    else:
        return redirect(url_for('login'))
#all posts read
@app.route('/allpost')
def allpost():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select postid,title,date from posts where added_by=%s order by date desc',[username])
        data=cursor.fetchall()
        print(data)
        cursor.close()
        return render_template('table.html',data=data)
    else:
        return redirect(url_for('login'))
#read/view
@app.route('/viewpost/<postid>')
def viewpost(postid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select title,content from posts where postid=%s',[postid])
        data=cursor.fetchone()
        cursor.close()
        title=data[0]
        content=data[1]
        return render_template('viewpost.html',title=title,content=content)
    else:
        return redirect(url_for('login'))
#delete
@app.route('/delete/<postid>')
def delete(postid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from posts where postid=%s',[postid])
        cursor.close()
        flash('post deleted')
        return redirect(url_for('allpost'))
    else:
        return redirect(url_for('login'))
#update
@app.route('/updatepost/<postid>',methods=['GET','POST'])
def updatepost(postid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select title,content from posts where postid=%s',[postid])
        data=cursor.fetchone()
        cursor.close()
        title=data[0]
        content=data[1]
        if request.method=='POST':
            title=request.form['title']
            content=request.form['content']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('update posts set title=%s,content=%s where postid=%s',[title,content,postid])
            mydb.commit()
            flash('post updated successfully')
            return redirect(url_for('allpost'))
        return render_template('updatepost.html',title=title,content=content)
    else:
        return redirect(url_for('login'))

app.run(debug=True,use_reloader=True)