import os
import aiml
import json
import requests
from flask import Flask

kernel = aiml.Kernel()

for filename in os.listdir("brain"):
    if filename.endswith(".aiml"):
        kernel.learn("brain/" + filename)


app = Flask(__name__)

@app.route("/<query>")
def index(query):
    if "ketersediaan" in query.lower() or "pengecekkan" in query.lower():
        #print("Masuk")
        jenis = 0
        sedia = query.lower()
        if "deluxe suite" in sedia:
            kamar = "Deluxe Suite"
            jenis = 3
        elif "club premiere" in sedia:
            kamar = "Club Premiere"
            jenis = 2
        elif "deluxe" in sedia:
            kamar = "Deluxe"
            jenis = 1

        tanggal = ""
        bulan = ""
        tahun = ""
        tanggalBenar = True
        if(sedia.count("-") != 2):
            tanggalBenar = False
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
                tanggalBenar = False
        #print(tanggal,bulan,tahun)
        if tanggalBenar and jenis!=0 :
            date = tahun+'-'+bulan+'-'+tanggal
            #print(date)
            king = 0
            twin = -1
            if jenis == 1:
                room_type = str(32)
                r = requests.get('https://staging-santika.oval.id/fastbooking-availabilty/?hotel=98&date='+ date +'&room_type='+ room_type +'&format=json')
                hasil = json.loads(r.content)
                #print(hasil)
                king = hasil["count"]
                room_type = str(33)
                r = requests.get('https://staging-santika.oval.id/fastbooking-availabilty/?hotel=98&date='+ date +'&room_type='+ room_type +'&format=json')
                hasil = json.loads(r.content)
                twin = hasil["count"]
            elif jenis == 2:
                room_type = str(34)
                r = requests.get('https://staging-santika.oval.id/fastbooking-availabilty/?hotel=98&date='+ date +'&room_type='+ room_type +'&format=json')
                hasil = json.loads(r.content)
                king = hasil["count"]
                room_type = str(35)
                r = requests.get('https://staging-santika.oval.id/fastbooking-availabilty/?hotel=98&date='+ date +'&room_type='+ room_type +'&format=json')
                hasil = json.loads(r.content)
                twin = hasil["count"]
            else:
                room_type = str(36)
                r = requests.get('https://staging-santika.oval.id/fastbooking-availabilty/?hotel=98&date='+ date +'&room_type='+ room_type +'&format=json')
                hasil = json.loads(r.content)
                #print(hasil)
                king = hasil["count"]
            message = '{ "message": "Kamar ' + kamar + ' yang tersedia pada tanggal ' + tanggal + '/' + bulan + '/' + tahun
            message = message + ' adalah ' + str(king) + ' kamar King Size'
            if twin != -1:
                message = message + ' dan ' + str(twin) + ' kamar Twin Size'
            message = message + '" }'
            return message
        else:
            #Output salah
            if jenis == 0:
                return '{ "message": "Input Kamar Salah" }'
            else:
                # print(kamar)
                return '{ "message": "Input Penanggalan Salah" }'

    else:
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
		if jumlah != 0:
		    objJson = objJson + "header: " + objJson.split('@')[0] + ","
        #objJson = str(response.find("?@"))
        #objJson = response[:5]
        objJson = objJson + '"ul": '+ str(jumlah) + ', "il": [ {"0": 1}'
        #tambah di "il" sesuai il di tiap ul yang ada
        jumlahIl = []
        indexIl = [[]for i in range(jumlah)]
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
                indexIl[i-1].append(response.find("@-",begin, endUl)+2)
                il = il + 1
                begin = response.find("-@",begin, endUl) + 3
                #print(objJson)
                #print(response.find("@-",begin, endUl),begin, end)
            objJson = objJson + ', {"'+str(i)+'": '+str(il) + "}"
            jumlahIl.append(il)
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
            for j in range(1, jumlahIl[i-1] + 1):
                begin = indexIl[i-1][j-1]
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

if __name__ == '__main__':
    app.run(debug=True)
