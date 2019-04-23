import os
import aiml
import json
from flask import Flask

kernel = aiml.Kernel()

for filename in os.listdir("brain"):
    if filename.endswith(".aiml"):
        kernel.learn("brain/" + filename)


app = Flask(__name__)

@app.route("/<query>")
def index(query):
    # Opening JSON
    response = kernel.respond(query)
    # Pengubahan string response ke dalam string bentuk JSON:
    # 1. Cek jumlah <ul> dan <li>
    # 2. sejumlah <ul> akan disimpan di JSON sebelum chat dari bot ada
    #    a. 0 berarti hanya kalimat
    #    b. n <ul> akan membuat jumlah objek di JSON
    objJson = "{"
    jumlah = response.count("@?")
    if jumlah == -1:
        jumlah = 0
    #objJson = str(response.find("?@"))
    #objJson = response[:5]
    objJson = objJson + '"ul": '+ str(jumlah) + ', "il": { "0":1'
    #tambah di "il" sesuai il di tiap ul yang ada
    jumlahIl = []
    indexIl = [[]for i in range(jumlah)]
    beginUl = 0
    #beginUl untuk <ul>
    endUl = len(response)
    # dilakukan sejumlah ul yang ada
    for i in range(1,jumlah+1):
        beginUl = response.find("@?",beginUl, endUl)
        #print(beginUl)
        #update beginUl di awal
        end = response.find("?@",beginUl, endUl)
        #end untuk </ul>
        begin = beginUl+1
        il = 0
        while response.find("@-",begin, endUl) < end-2 and response.find("@-",begin, endUl) != -1:
            #cari jumlah il di tiap ul
            #print(response.find("@-",begin, endUl))
            #print(response[begin:end])
            indexIl[i-1].append(response.find("@-",begin, endUl)+2)
            il = il + 1
            begin = response.find("-@",begin, endUl) + 3
            #print(objJson)
            #print(response.find("@-",begin, endUl),begin, end)
        objJson = objJson + ', "'+str(i)+'": '+str(il)
        jumlahIl.append(il)
        beginUl = end + 2
        #beginUl untuk cari <ul> baru lagi kalau ada
    #print(indexIl)
    
    #tutup il
    begin = 0
    end = len(response)
    objJson = objJson + '}, "message":{"0": "'
    if jumlah == 0:
        #print(response)
        objJson = objJson + response
    elif jumlah != 1:
        end = response.find("@^")
        objJson = objJson + response[0:end]
    print(end)
    #print(response.find("\n",0, len(response)))
    objJson = objJson + '"' # tutup message "0": ""
    
    begin = end+3
    
    #masukkan ke message
    for i in range(1, jumlah+1):
        #i untuk tiap ul yang ada
        end = len(response)
        objJson = objJson + ',"'+str(i)+'": {"0": "'
        #message '0' judul ul
        end = response.find("@?",begin, end)-1 #karena ada spasi
        objJson = objJson + response[begin:end] + '"'
        for j in range(1, jumlahIl[i-1] + 1):
            begin = indexIl[i-1][j-1]
            end = response.find("-@",begin,len(response))
            #message per li:
            objJson = objJson + ', "'+str(j)+'": "' + response[begin:end] + '" '
        begin = response.find("?@",begin, len(response)) + 3
        objJson = objJson + '}'
    
    # tutup message + Closing JSON
    objJson = objJson + "}}"
    # JSONify objJson untuk return objek dalam bentuk JSON
    return objJson

    
if __name__ == '__main__':
    app.run(debug=True)
