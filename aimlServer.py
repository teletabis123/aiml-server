import os
import aiml
import json
import requests
from flask import Flask

kernel = aiml.Kernel()

#if os.path.isfile("bot_brain.brn"):
#    kernel.bootstrap(brainFile = "bot_brain.brn")
#else:
kernel.bootstrap(learnFiles = "std-startup.xml", commands = "load aiml b")
kernel.saveBrain("bot_brain.brn")

app = Flask(__name__)

tanggal = ""
bulan = ""
tahun = ""

def cekQuery(response):
    if response[:2] == "@@":
        return True
    else:
        return False

def getMaxHari(bulan):
    if bulan == "02":
        if(int(tahun) % 4 == 0):
            return 29
        else:
            return 28
    else:
        if bulan == "04" or bulan == "06" or bulan == "09" or bulan == "11":
            return 30
        else:
            return 31

def cekPenanggalan(sedia):
    global tanggal
    global bulan
    global tahun
    
    if(sedia.count("-") != 2):
        return False
    else:
        indexTanggalAkhir = sedia.find("-",0,len(sedia))
        indexTanggalAwal = indexTanggalAkhir - 2
        indexBulanAwal = indexTanggalAkhir + 1
        indexBulanAkhir = sedia.find("-",indexBulanAwal,len(sedia))
        indexTahunAwal = indexBulanAkhir + 1
        indexTahunAkhir = sedia.find(" ",indexTahunAwal,len(sedia))
        if indexTahunAkhir == -1:
            indexTahunAkhir = len(sedia)
        tanggal = sedia[indexTanggalAwal:indexTanggalAkhir]
        bulan = sedia[indexBulanAwal:indexBulanAkhir]
        if indexTahunAkhir == -1:
            tahun = sedia[indexTahunAwal:]
        else:
            tahun = sedia[indexTahunAwal:indexTahunAkhir]
        #print(kamar,tanggal,bulan,tahun)
        if(not(tanggal.isnumeric() and bulan.isnumeric() and tahun.isnumeric()) or not(len(tanggal)==2 and len(bulan)==2 and len(tahun)==4)):
            return False
        maxHari = getMaxHari(bulan)
        #print(maxHari)
        if int(tanggal) < 0 or int(tanggal) > maxHari:
            return False
    return True

def getRequestContent(date, room_type):
    r = requests.get('https://staging-santika.oval.id/fastbooking-availabilty/?hotel=98&date='+ date +'&room_type='+ room_type +'&format=json')
    return json.loads(r.content)

def messageAvailability(sedia):
    jenis = 0
    
    if "deluxe suite" in sedia:
        kamar = "Deluxe Suite"
        jenis = 3
    elif "club premiere" in sedia:
        kamar = "Club Premiere"
        jenis = 2
    elif "deluxe" in sedia:
        kamar = "Deluxe"
        jenis = 1

    tanggalBenar = True
    tanggalBenar = cekPenanggalan(sedia)
                
    #print(tanggal,bulan,tahun)
    if tanggalBenar and jenis!=0 :
        date = tahun+'-'+bulan+'-'+tanggal
        #print(date)
        king = 0
        twin = -1
        if jenis == 1:
            room_type = str(32)
            #r = requests.get('https://staging-santika.oval.id/fastbooking-availabilty/?hotel=98&date='+ date +'&room_type='+ room_type +'&format=json')
            hasil = getRequestContent(date,room_type)
            #print(hasil)
            king = hasil["count"]
            room_type = str(33)
            #r = requests.get('https://staging-santika.oval.id/fastbooking-availabilty/?hotel=98&date='+ date +'&room_type='+ room_type +'&format=json')
            hasil = getRequestContent(date,room_type)
            twin = hasil["count"]
        elif jenis == 2:
            room_type = str(34)
            #r = requests.get('https://staging-santika.oval.id/fastbooking-availabilty/?hotel=98&date='+ date +'&room_type='+ room_type +'&format=json')
            hasil = getRequestContent(date,room_type)
            king = hasil["count"]
            room_type = str(35)
            #r = requests.get('https://staging-santika.oval.id/fastbooking-availabilty/?hotel=98&date='+ date +'&room_type='+ room_type +'&format=json')
            hasil = getRequestContent(date,room_type)
            twin = hasil["count"]
        else:
            room_type = str(36)
            #r = requests.get('https://staging-santika.oval.id/fastbooking-availabilty/?hotel=98&date='+ date +'&room_type='+ room_type +'&format=json')
            hasil = getRequestContent(date,room_type)
            #print(hasil)
            king = hasil["count"]
        message = '{ "message": "Kamar ' + kamar + ' yang tersedia pada tanggal ' + tanggal + '-' + bulan + '-' + tahun
        message = message + ' adalah ' + str(king) + ' kamar King Size'
        if twin != -1:
            message = message + ' dan ' + str(twin) + ' kamar Twin Size'
        message = message + '" }'
        return message
    else:
        #Output salah
        if jenis == 0:
            return '{ "message": "Format pengecekkan kamar salah" }'
        else:
            # print(kamar)
            return '{ "message": "Format tanggal yang anda masukkan salah" }'

def jumlahUl(response):
    return response.count("@?")

def messageChat(response):
    objJson = "{"
    jumlah = jumlahUl(response)
    if jumlah == -1:
        jumlah = 0
    if jumlah != 0:
        keep = response.split('@?')[0]
        print(keep)
        objJson = objJson + '"header" :"' + keep.strip() + '",'
    #objJson = str(response.find("?@"))
    #objJson = response[:5]
    objJson = objJson + '"ul": '+ str(jumlah) + ', "il": [ {"0": 1}'
    #tambah di "il" sesuai il di tiap ul yang ada
    jumlahLi = []
    indexLi = [[]for i in range(jumlah)]
    beginUl = 0
    #beginUl untuk <ul>
    endUl = len(response)
    il = 0
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
            indexLi[i-1].append(response.find("@-",begin, endUl)+2)
            il = il + 1
            begin = response.find("-@",begin, endUl) + 3
            #print(objJson)
            #print(response.find("@-",begin, endUl),begin, end)
        objJson = objJson + ', {"'+str(i)+'": '+str(il) + "}"
        jumlahLi.append(il)
        beginUl = end + 2
        #beginUl untuk cari <ul> baru lagi kalau ada
    #print(indexIl)
    
    #tutup il
    begin = 0
    end = len(response)
    objJson = objJson + ' ], "message": [ {"0": "'
    if jumlah == 0:
        #print(response)
        objJson = objJson + response
    elif jumlah != 1:
        end = response.find("@^")
        objJson = objJson + response[0:end]
    #print(end)
    #print(response.find("\n",0, len(response)))
    #objJson = objJson + il > 0 ? '"}' : '"}]' # tutup message "0": ""
    if il == 0: # tutup message "0": ""
        objJson = objJson + '"}]'
    else:
        objJson = objJson + '"}'
    
    begin = end+3
    
    #masukkan ke message
    for i in range(1, jumlah+1):
        #i untuk tiap ul yang ada
        end = len(response)
        objJson = objJson + ', {"'+str(i)+'": [ {"0": "'
        #message '0' judul ul
        end = response.find("@?",begin, end)-1 #karena ada spasi
        objJson = objJson + response[begin:end] + '"}'
        for j in range(1, jumlahLi[i-1] + 1):
            begin = indexLi[i-1][j-1]
            end = response.find("-@",begin,len(response))
            #message per li:
            objJson = objJson + ', {"'+str(j)+'": "' + response[begin:end] + '"} '
        begin = response.find("?@",begin, len(response)) + 3
        objJson = objJson + ']'
    
    # tutup message + Closing JSON
    if il == 0: # tutup message "0": ""
        objJson = objJson + '}'
    else:
        objJson = objJson + '}]}'
    #objJson = objJson + " }"
    # JSONify objJson untuk return objek dalam bentuk JSON
    return objJson

@app.route("/<query>")
def index(query):
    # Opening JSON
    response = kernel.respond(query)
    # Pengubahan string response ke dalam string bentuk JSON:
    # 1. Cek jumlah <ul> dan <li>
    # 2. sejumlah <ul> akan disimpan di JSON sebelum chat dari bot ada
    #    a. 0 berarti hanya kalimat
    #    b. n <ul> akan membuat jumlah objek di JSON
    #print(response)
    if cekQuery(response):
        sedia = query.lower()
        return messageAvailability(sedia)
    else:
        return messageChat(response)


if __name__ == '__main__':
    app.run(debug=True)
