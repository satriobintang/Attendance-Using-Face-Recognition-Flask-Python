# Created By Alt5chm3rz
# https://github.com/satriobintang/Attendance-Using-Face-Recognition-Flask-Python
# January 2023

import cv2
import os
from flask import Flask,request,render_template
from datetime import date
from datetime import datetime
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
import pandas as pd
import joblib

app = Flask(__name__)

class Attendance:
    def __init__(self):
        self.datetoday = date.today().strftime("%m_%d_%y")
        self.datetoday2 = date.today().strftime("%d-%B-%Y")
        self.face_detector = cv2.CascadeClassifier('static/haarcascade_frontalface_default.xml')
        self.cap = cv2.VideoCapture(0)
        
        if not os.path.isdir('Attendance'):
            os.makedirs('Attendance')
        if not os.path.isdir('static/faces'):
            os.makedirs('static/faces')
        if f'Attendance-{self.datetoday}.csv' not in os.listdir('Attendance'):
            with open(f'Attendance/Attendance-{self.datetoday}.csv','w') as f:
                f.write('Name,Roll,Time')

    def totalreg(self):
        return len(os.listdir('static/faces'))
    
    def extract_faces(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_points = self.face_detector.detectMultiScale(gray, 1.3, 5)
        return face_points
    
    def identify_face(self, facearray):
        model = joblib.load('static/face_recognition_model.pkl')
        return model.predict(facearray)

    def train_model(self):
        faces = []
        labels = []
        userlist = os.listdir('static/faces')
        for user in userlist:
            for imgname in os.listdir(f'static/faces/{user}'):
                img = cv2.imread(f'static/faces/{user}/{imgname}')
                resized_face = cv2.resize(img, (50, 50))
                faces.append(resized_face.ravel())
                labels.append(user)
        faces = np.array(faces)
        knn = KNeighborsClassifier(n_neighbors=5)
        knn.fit(faces,labels)
        joblib.dump(knn,'static/face_recognition_model.pkl')
    
    def extract_attendance(self):
        df = pd.read_csv(f'Attendance/Attendance-{self.datetoday}.csv')
        names = df['Name']
        rolls = df['Roll']
        times = df['Time']
        l = len(df)
        return names,rolls,times,l
    
    def add_attendance(self, name):
        username = name.split('_')[0]
        userid = name.split('_')[1]
        current_time = datetime.now().strftime("%H:%M:%S")

        df = pd.read_csv(f'Attendance/Attendance-{self.datetoday}.csv')
        if (userid) not in list(df['Roll']):
                with open(f'Attendance/Attendance-{self.datetoday}.csv','a') as f:
                    f.write(f'\n{username},{userid},{current_time}')

#================ ROUTING KE TAMPILAN HOME  ================#
attendance = Attendance()
#HALAMAN AWAL
@app.route('/')
def home():
    names,rolls,times,l = attendance.extract_attendance()    
    return render_template('home.html',names=names,rolls=rolls,times=times,l=l,totalreg=attendance.totalreg(),datetoday2=attendance.datetoday2) 

#================ MEMBUKA WEBCAM DAN MELAKUKAN FACE RECOGNITION  ================#
@app.route('/start',methods=['GET'])
def start():
    if 'face_recognition_model.pkl' not in os.listdir('static'):
        return render_template('home.html',totalreg=attendance.totalreg(),datetoday2=attendance.datetoday2,mess='Tidak ada model terlatih di folder statis. Tambahkan wajah baru untuk melanjutkan.') 

    cap = cv2.VideoCapture(0)
    ret = True
    while ret:
        ret,frame = cap.read()
        if attendance.extract_faces(frame)!=():
            (x,y,w,h) = attendance.extract_faces(frame)[0]
            cv2.rectangle(frame,(x, y), (x+w, y+h), (255, 0, 20), 2)
            face = cv2.resize(frame[y:y+h,x:x+w], (50, 50))
            identified_person = attendance.identify_face(face.reshape(1,-1))[0]
            attendance.add_attendance(identified_person)
            cv2.putText(frame,f'{identified_person}',(30,30),cv2.FONT_HERSHEY_SIMPLEX,1,(255, 0, 20),2,cv2.LINE_AA)
        cv2.imshow('Attendance',frame)
        if cv2.waitKey(1)==27:
            break
    cap.release()
    cv2.destroyAllWindows()
    names,rolls,times,l = attendance.extract_attendance()    
    return render_template('home.html',names=names,rolls=rolls,times=times,l=l,totalreg=attendance.totalreg(),datetoday2=attendance.datetoday2) 

#================ MENAMBAHKAN MAHASISWA BARU  ================#
@app.route('/add',methods=['GET','POST'])
def add():
    newusername = request.form['newusername']
    newuserid = request.form['newuserid']
    userimagefolder = 'static/faces/'+newusername+'_'+str(newuserid)
    if not os.path.isdir(userimagefolder):
        os.makedirs(userimagefolder)
    cap = cv2.VideoCapture(0)
    i,j = 0,0
    while 1:
        _,frame = cap.read()
        faces = attendance.extract_faces(frame)
        for (x,y,w,h) in faces:
            cv2.rectangle(frame,(x, y), (x+w, y+h), (255, 0, 20), 2)
            cv2.putText(frame,f'Images Captured: {i}/50',(30,30),cv2.FONT_HERSHEY_SIMPLEX,1,(255, 0, 20),2,cv2.LINE_AA)
            if j%10==0:
                name = newusername+'_'+str(i)+'.jpg'
                cv2.imwrite(userimagefolder+'/'+name,frame[y:y+h,x:x+w])
                i+=1
            j+=1
        if j==500:
            break
        cv2.imshow('Memfoto Mahasiswa Baru Untuk Data Training',frame)
        if cv2.waitKey(1)==27:
            break
    cap.release()
    cv2.destroyAllWindows()
    print('Model Pelatihan Wajah')
    attendance.train_model()
    names,rolls,times,l = attendance.extract_attendance()    
    return render_template('home.html',names=names,rolls=rolls,times=times,l=l,totalreg=attendance.totalreg(),datetoday2=attendance.datetoday2) 

#================ FUNGSI UNTUK MENJALANKAN FLASK ================#
if __name__ == '__main__':
    app.run(debug=True)