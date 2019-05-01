import os
import aiml
import json
import requests
from flask import Flask

# Set up AIML Kernel dari library aiml
kernel = aiml.Kernel()
kernel.bootstrap(learnFiles = "std-startup.xml", commands = "load aiml b")
kernel.saveBrain("bot_brain.brn")

app = Flask(__name__)

tanggal = ""
bulan = ""
tahun = ""

# Function untuk mengecek response dari query yang didapatkan.
# Bernilai True bila mencari availability kamar hotel.
# Bernilai False bila merupakan chat biasa.
def cekQuery(response):
    if response[:2] == "@@":
        return True
    else:
        return False

# Function untuk mengetahui maximal hari dari suatu bulan tertentu
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

# Function untuk melakukan pengecekkan input penanggalan dari user bila mencari availability kamar hotel
# Input Penanggalan yang benar: DD-MM-YYYY
def cekPenanggalan(sedia):
    global tanggal
    global bulan
    global tahun
    
    if(sedia.count("-") != 2):
        return False
    else:
        # Menentukan tanggal, bulan, dan tahun dari response
        # akan mengecek syntax penanggalan
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
        if(not(tanggal.isnumeric() and bulan.isnumeric() and tahun.isnumeric()) or not(len(tanggal)==2 and len(bulan)==2 and len(tahun)==4)):
            return False
        maxHari = getMaxHari(bulan)
        if int(tanggal) < 1 or int(tanggal) > maxHari or int(bulan) < 1 or int(bulan) > 12:
            return False
    return True

# Function untuk melakukan request ke API santika untuk mengecek availability kamar hotel
def getRequestContent(date, room_type):
    r = requests.get('https://staging-santika.oval.id/fastbooking-availabilty/?hotel=98&date='+ date +'&room_type='+ room_type +'&format=json')
    return json.loads(r.content)

# Function untuk mengembalikan message untuk availability kamar hotel
# menentukan kamar yang diminta dan tanggal dari yang penanggalan yang benar
# request ke API dan mengembalikan message availability
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
    if tanggalBenar and jenis!=0 :
        date = tahun+'-'+bulan+'-'+tanggal
        king = 0
        twin = -1
        if jenis == 1:
            room_type = str(32)
            hasil = getRequestContent(date,room_type)
            king = hasil["count"]
            room_type = str(33)
            hasil = getRequestContent(date,room_type)
            twin = hasil["count"]
        elif jenis == 2:
            room_type = str(34)
            hasil = getRequestContent(date,room_type)
            king = hasil["count"]
            room_type = str(35)
            hasil = getRequestContent(date,room_type)
            twin = hasil["count"]
        else:
            room_type = str(36)
            hasil = getRequestContent(date,room_type)
            king = hasil["count"]
        message = '{ "message": "Kamar ' + kamar + ' yang tersedia pada tanggal ' + tanggal + '-' + bulan + '-' + tahun
        message = message + ' adalah ' + str(king) + ' kamar King Size'
        if twin != -1:
            message = message + ' dan ' + str(twin) + ' kamar Twin Size'
        message = message + '" }'
        return message
    else: # bila input salah
        if jenis == 0:
            return '{ "message": "Format pengecekkan kamar salah" }'
        else:
            return '{ "message": "Format tanggal yang anda masukkan salah" }'

# UL adalah penunjuk berapa banyak bulleting di message
# Function untuk mengetahui jumlah UL yang ada di return message
def jumlahUl(response):
    return response.count("@?")

# Function untuk mengembalikan message chat selain availability kamar hotel
# akan memisah-misahkan bagian-bagian dari response
# bentuk tiap-tiap jumlah ul akan berbeda juga sesuai li
def messageChat(response):
    # Pembuka message yang dikembalikan
    objJson = "{"
    jumlah = jumlahUl(response)
    # Untuk membentuk message yang memberitahukan jumlah ul, dan li dari ul ke-0
    objJson = objJson + '"ul": '+ str(jumlah) + ', "il": [ {"0": 1}'
    # Untuk menaruh di message jumlah list(li) yang ada di tiap bulleting(ul) yang ada
    jumlahLi = [] # untuk menyimpan list yang ada
    indexLi = [[]for i in range(jumlah)] # untuk menyimpan index awal dari tiap list di response, Array 2D untuk tiap ul
    beginUl = 0 # untuk menyimpan index pertama dari ul
    endUl = len(response) # untuk menyimpan index terakhir dari message, index terakhir
    il = 0
    # untuk mencari li dan indexnya
    for i in range(1,jumlah+1): # sejumlah ul yang ada di response
        beginUl = response.find("@?",beginUl, endUl) # beginUl diawali dari @? untuk tiap ul
        end = response.find("?@",beginUl, endUl) # end untuk index terakhir di ul yang terkait (1 ul dengan ^)
        begin = beginUl+1 # begin untuk menyimpan index pertama untuk pencarian li, sebagai temp
        il = 0 # jumlah li yang ada diinisialisasi dengan nilai 0
        while response.find("@-",begin, endUl) < end-2 and response.find("@-",begin, endUl) != -1: # mencari li sampai dengan li ada di sebelum penutup ul
            # untuk tiap li ada di ul bersangkutan
            indexLi[i-1].append(response.find("@-",begin, endUl)+2) # menambah index awal dari tiap li
            il = il + 1 # jumlah li ditambah sesuai li yang ada
            begin = response.find("-@",begin, endUl) + 3 # mengubah index temp untuk mencari li selanjutnya
        # menyimpan jumlah li yang ada di tiap ul
        objJson = objJson + ', {"'+str(i)+'": '+str(il) + "}"
        jumlahLi.append(il)
        beginUl = end + 2 # mengubah beginUl menjadi index ul selanjutnya bila ada
    # menyimpan message dari response
    end = len(response) # temp untuk menyimpan akhir range dari message yang akan disimpan
    objJson = objJson + ' ], "message": [ {"0": "' # penutup ul li dan pembuka message yang akan disimpan
    # untuk menyimpan message awal
    if jumlah == 0: # untuk menyimpan message bila tidak ada bulleting
        objJson = objJson + response # langsung menyimpan semua response yang ada
    elif jumlah != 1: # untuk menyimpan message awal sebelum masuk ke bulleting
        end = response.find("@^") # untuk menyimpan index terakhir dari message
        objJson = objJson + response[0:end]
    #else:
     #   end = response.find("@-")
      #  objJson = objJson + response[0:end]
    # untuk menutup message awal
    if il == 0: # tutup message tidak ada ul, berarti tutup message
        objJson = objJson + '"}]'
    else: # message belum ditutup, masih ada message dari li
        objJson = objJson + '"}'
    begin = end+3 # temp untuk menyimpan awal ul
    #masukkan ke message
    for i in range(1, jumlah+1): # untuk tiap ul yang ada
        end = len(response) # penanda penutup ul
        objJson = objJson + ', {"'+str(i)+'": [ {"0": "' # untuk membuka message untuk ul ke i
        #message '0' judul ul
        if(jumlah == 1):
            begin = 0
        end = response.find("@?",begin, end)-1 # index pembuka message di start ul
        objJson = objJson + response[begin:end] + '"}' # menyimpan message awal ul
        # menyimpan message di tiap li
        for j in range(1, jumlahLi[i-1] + 1): # sebanyak li yang ada
            begin = indexLi[i-1][j-1] # index awal berdasarkan yang telah disimpan
            end = response.find("-@",begin,len(response)) # -@ penanda li berhenti
            objJson = objJson + ', {"'+str(j)+'": "' + response[begin:end] + '"} ' # menyimpan message tiap li
        begin = response.find("?@",begin, len(response)) + 3 # diperbarui untuk ul selanjutnya bila ada
        objJson = objJson + ']}' # penutup li di ul
    
    # menutup message yang akan dikembalikan
    if il == 0: # tutup message bila tidak ada bulleting
        objJson = objJson + '}'
    else: # tutup message bila ada bulleting
        objJson = objJson + ']}'
    # Mengembalikan message
    return objJson

# Function Main
@app.route("/<query>")
def index(query):
    # query = input chat
    # Meminta hasil response dari query berdasarkan AIML
    response = kernel.respond(query)
    # Menentukan jenis message yang akan dikembalikan
    if cekQuery(response):
        sedia = query.lower()
        return messageAvailability(sedia)
    else:
        return messageChat(response)

if __name__ == '__main__':
    app.run(debug=True)
