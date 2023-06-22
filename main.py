import streamlit as st
import pandas as pd
import numpy as np
import warnings                    
warnings.filterwarnings("ignore")
from nltk.tokenize import word_tokenize
from nltk import pos_tag
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.preprocessing import LabelEncoder
from collections import defaultdict
from nltk.corpus import wordnet as wn
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn import model_selection, svm
from sklearn.metrics import accuracy_score
import nltk
import pickle 
import csv



#To Hide Warnings
st.set_option('deprecation.showfileUploaderEncoding', False)
st.set_option('deprecation.showPyplotGlobalUse', False)

#Load Model NB from disk
loaded_model_nb = pickle.load(open('finalized_model_NB.sav', 'rb'))

# read the processed data
dp = pd.read_csv('processed_data_vol2.csv', encoding='cp1252')
                # With Tfidf Vectorizer

Tfidf_vect = TfidfVectorizer()
Tfidf_vect.fit(dp['text_final'])
# Security
#passlib,hashlib,bcrypt,scrypt
import hashlib
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password,hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False
# DB Management
import sqlite3 
conn = sqlite3.connect('data.db')
c = conn.cursor()
# DB  Functions
def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT,password TEXT, status INTEGER)')


def add_userdata(username,password):
    c.execute('INSERT INTO userstable(username,password, status) VALUES (?,?,?)',(username,password, 0))
    conn.commit()
    
def blocked_user(username, count):
    c.execute('UPDATE userstable SET status = ? WHERE username = ?',(count, username))
    conn.commit()
    print("blocked")
    
def unblocked_user(username):
    c.execute('UPDATE userstable SET status = ? WHERE username = ?',(0, username))
    conn.commit()

def login_user(username,password):
    c.execute('SELECT * FROM userstable WHERE username =? AND password = ? AND status < ?',(username,password, 4))
    data = c.fetchall()
    return data


def view_all_users():
    c.execute('SELECT username FROM userstable WHERE status > ?',(3,))
    data = c.fetchall()
    return data

def block_count(user):
    c.execute('SELECT status FROM userstable WHERE username = ?',user)
    data = c.fetchall()
    return data


def predictInput(new_input):

    new_input_Tfidf = Tfidf_vect.transform(new_input) # vectorize input
    # Naive Bayes prediction
    new_output_nb = loaded_model_nb.predict(new_input_Tfidf)
    # configure the prediction labels
    return new_output_nb

def main():
    """ Common ML Dataset Explorer """
    # Heading
    st.header("Hate Speech Detection using Machine Learning")
    st.subheader("Login and start Detection")
    menu = ["SignUp","Login", "Admin Dashboard"]
    choice = st.sidebar.selectbox("Menu",menu)

    if choice == "Login":
        username = st.sidebar.text_input("User Name")
        password = st.sidebar.text_input("Password",type='password')
        if st.sidebar.checkbox("Login/Logout"):
            # if password == '12345':
            create_usertable()
            hashed_pswd = make_hashes(password)
            result = login_user(username,check_hashes(password,hashed_pswd))
            if result:
                
                st.success("Logged In as {}".format(username))
                st.sidebar.success("login Success.")
                # Define the image URL
                image_url = "social-media.jpg"

                # Define a list to store the comments
                comments = []


                # Display the image
                st.image(image_url)

                # Create an input box for users to input their comments
                comment_input = st.text_input("Add your comment")


                # Create a button to submit the comment
                if st.button("Submit"):
                    comments.append(comment_input)
                    

                
                # Display the comments

                if comments:
                    st.write("### Comments:")
                    result = predictInput(comments)
                    if result[0]==1:
                        st.info(comments[0])
                    else:
                        st.error("Hateful Comment Detected...", icon="⚠️")
                        print(username)
                        i= block_count((username,))
                        print(i[0][0])
                        i = int(i[0][0])+1
                        blocked_user(username, i)
                else:
                    st.write("No comments yet.")
    
            else:
                st.error("Login Failed or Account Blocked")
                
    elif choice == "SignUp":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password",type='password')

        if st.button("Signup"):
            create_usertable()
            add_userdata(new_user,make_hashes(new_password))
            st.success("You have successfully created a valid Account")
            st.info("Go to Login Menu to login")
    
    elif choice == "Admin Dashboard":
        username = st.sidebar.text_input("User Name")
        password = st.sidebar.text_input("Password",type='password')
        if st.sidebar.checkbox("Login / Logout"):
            if username == "admin" and password=="admin":
                st.success("Logged In as 'Admin'")
                l = view_all_users()
                if(len(l)>0):
                    choice2 = st.selectbox("Blocked Users",list(l[0]))
                    if st.button("Unblocked"):
                        unblocked_user(choice2)
                        st.success("User {} Unblocked.".format(username))
                else:
                    st.info("No Blocked user found in Database.")

if __name__ == '__main__':
    main()