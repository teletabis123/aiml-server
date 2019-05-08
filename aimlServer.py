import os
import re
import aiml
import json
import requests
import datetime
from flask import Flask
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from itertools import groupby


# Set up AIML Kernel dari library aiml
kernel = aiml.Kernel()
kernel.bootstrap(learnFiles = "std-startup.xml", commands = "load aiml b")
kernel.saveBrain("bot_brain.brn")

app = Flask(__name__)

tanggal = ""
bulan = ""
tahun = ""
strBulan = ""
email = ""
isemail = False

# Function untuk mengecek response dari query yang didapatkan.
# Bernilai True bila mencari availability kamar hotel.
# Bernilai False bila merupakan chat biasa.
def cekQuery(response):
    if response.find("[request]",0,len(response)) != -1:
        return True
    else:
        return False
    
def getBulan(bln):
    if bln == "januari" or bln == "january":
        return "01"
    elif bln == "februari" or bln == "february":
        return "02"
    elif bln == "maret" or bln == "march":
        return "03"
    elif bln == "april":
        return "04"
    elif bln == "mei" or bln == "may":
        return "05"
    elif bln == "juni" or bln == "june":
        return "06"
    elif bln == "juli" or bln == "july":
        return "07"
    elif bln == "agustus" or bln == "august":
        return "08"
    elif bln == "september":
        return "09"
    elif bln == "oktober" or bln == "october":
        return "10"
    elif bln == "november" or bln == "nopember":
        return "11"
    elif bln == "desember" or bln == "december":
        return "12"
    else:
        return bln

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
def cekPenanggalan(sedia, tgl, bln, thn):
    global tanggal
    global bulan
    global tahun
    global strBulan
    
    strBulan = bln.capitalize()
    dateNow = datetime.datetime.now()
    
    # Menentukan tanggal, bulan, dan tahun dari response
    # akan mengecek syntax penanggalan
    tanggal = str(tgl)
    bulan = getBulan(bln)     
    tahun = str(thn)

    if(len(tanggal) == 1):
        tanggal = "0"+tanggal

    #print(tanggal,bulan,tahun)

    if(not(tanggal.isdigit() and bulan.isdigit() and tahun.isdigit()) or not(len(tanggal)==2 and len(bulan)==2 and len(tahun)==4)):
        print(tanggal)
        return False
    if int(tahun) < dateNow.year: #input year < year now
        print(dateNow.year)
        return False
    else: #input year >= year now
        if int(bulan) < dateNow.month and int(tahun) == dateNow.year: #input month < month now
            print(dateNow.month)
            return False
        else: #
            if int(tanggal) < dateNow.day and int(bulan) == dateNow.month and int(tahun) == dateNow.year:
                print(dateNow.day)
                return False
    maxHari = getMaxHari(bulan)
    if int(tanggal) < 1 or int(tanggal) > maxHari or int(bulan) < 1 or int(bulan) > 12:
        return False
    return True

# Function untuk melakukan request ke API santika untuk mengecek availability kamar hotel
def getRequestContent(room_type, date, jumlah_malam, jumlah_kamar):
    r = requests.get('https://staging-santika.oval.id/fastbooking-availabilty/?hotel=98&date='+ date +'&room_type='+ room_type +'&format=json')
    room = json.loads(r.content)
    room = room["count"]
    
    r = requests.get('https://staging-santika.oval.id/hotels/availability/?id=98&checkin_date='+ date +'&duration='+ str(jumlah_malam) +'&format=json')
    room = json.loads(r.content)
    room = room["results"][0]["available_flag"]
    if room:
        r = requests.get('https://staging-santika.oval.id/room-types/availability/?hotel=98&checkin_date='+ date +'&duration='+ str(jumlah_malam) +'&format=json')
        room = json.loads(r.content)
        kamar = 0
        if room_type == "36": #deluxe suite
            temp = room["results"][4]["rate_plan"]
            for i in range(0,len(temp)):
                if temp[i]["available_quota"] is not None and temp[i]["available_quota"] != 0:
                    kamar += temp[i]["available_quota"]
        elif room_type == "34": #club premiere
            temp = room["results"][3]["rate_plan"]
            for i in range(0,len(temp)):
                if temp[i]["available_quota"] is not None and temp[i]["available_quota"] != 0:
                    kamar += temp[i]["available_quota"]
            temp = room["results"][2]["rate_plan"]
            for i in range(0,len(temp)):
                if temp[i]["available_quota"] is not None and temp[i]["available_quota"] != 0:
                    kamar += temp[i]["available_quota"]
        elif room_type == "32": #deluxe
            temp = room["results"][1]["rate_plan"]
            for i in range(0,len(temp)):
                if temp[i]["available_quota"] is not None and temp[i]["available_quota"] != 0:
                    kamar += temp[i]["available_quota"]
            temp = room["results"][0]["rate_plan"]
            for i in range(0,len(temp)):
                if temp[i]["available_quota"] is not None and temp[i]["available_quota"] != 0:
                    kamar += temp[i]["available_quota"]
        return kamar
    else:
        return 0

# Function untuk mengembalikan message untuk availability kamar hotel
# menentukan kamar yang diminta dan tanggal dari yang penanggalan yang benar
# request ke API dan mengembalikan message availability
def messageAvailability(sedia):
    message = '{"ul": 0, "li": [ {"0": 1} ], "footer": [ {"0": 0} ], "message": [ {"0": "'
    jenis = 0
    tanggalBenar = True
    messageBenar = True
    jumlah_malam = 0
    jumlah_kamar = 0
    total_kamar = 0
    
    list_int = [int(''.join(i)) for is_digit, i in groupby(sedia, str.isdigit) if is_digit]
    
    # cek kamar
    if "deluxesuite" in sedia:
        kamar = "Deluxe Suite"
        jenis = 3
    elif "clubpremiere" in sedia:
        kamar = "Club Premiere"
        jenis = 2
    elif "deluxe" in sedia:
        kamar = "Deluxe"
        jenis = 1
    
    # cek tanggal
    if(len(list_int)) != 4:
        tanggalBenar = False
        messageBenar = False
    else:
        bln = sedia[sedia.find(str(list_int[0]),0,len(sedia))+len(str(list_int[0])) : sedia.find(str(list_int[1]),0,len(sedia))]
        jumlah_malam = list_int[2]
        jumlah_kamar = list_int[3]
        tanggalBenar = cekPenanggalan(sedia, list_int[0], bln, list_int[1])
    
    # cek ketersediaan
    if tanggalBenar and jenis!=0 :
        date = tahun+'-'+bulan+'-'+tanggal
        if jenis == 1:
            room_type = str(32)
        elif jenis == 2:
            room_type = str(34)
        else:
            room_type = str(36)
        total_kamar = getRequestContent(room_type, date, jumlah_malam, jumlah_kamar)
        if(total_kamar < jumlah_kamar): # kamar tidak cukup
            message = message + 'Kamar ' + kamar + ' pada tanggal ' + tanggal + ' ' + strBulan + ' ' + tahun + ' untuk ' + str(jumlah_kamar) + ' kamar untuk ' + str(jumlah_malam) + ' malam tidak tersedia'
        else:
            message = message + 'Kamar ' + kamar + ' pada tanggal ' + tanggal + ' ' + strBulan + ' ' + tahun + ' untuk ' + str(jumlah_kamar) + ' kamar untuk ' + str(jumlah_malam) + ' malam tersedia'
    else: # bila input salah
        if not messageBenar:
            message = message + 'Input kamar, tanggal, jumlah malam, atau jumlah kamar salah'
        elif jenis == 0:
            message = message + 'Format pengecekkan kamar salah'
        else:
            message = message + 'Format tanggal yang anda masukkan salah'
    if jumlah_kamar > 10 :
        message = message + ". Untuk pemesanan kamar diatas 10, mohon hubungi Sales dengan perihal Group Checkin"
    message = message + '" }], "m_footer": [ {"0": ""} ] }'
    return message

# UL adalah penunjuk berapa banyak bulleting di message
# Function untuk mengetahui jumlah UL yang ada di return message
def jumlahUl(response):
    return response.count("[ul]")

# Function untuk mengembalikan message chat selain availability kamar hotel
# akan memisah-misahkan bagian-bagian dari response
# bentuk tiap-tiap jumlah ul akan berbeda juga sesuai li
def messageChat(response):
    # Pembuka message yang dikembalikan
    objJson = "{"
    jumlah = jumlahUl(response)
    # Untuk membentuk message yang memberitahukan jumlah ul, dan li dari ul ke-0
    objJson = objJson + '"ul": '+ str(jumlah) + ', "li": [ {"0": 1}'
    # Untuk menaruh di message jumlah list(li) yang ada di tiap bulleting(ul) yang ada
    jumlahLi = [] # untuk menyimpan list yang ada
    jumlahFooter = [] # untuk menyimpan list yang ada
    indexLi = [[]for i in range(jumlah)] # untuk menyimpan index awal dari tiap list di response, Array 2D untuk tiap ul
    indexFooter = []; # untuk menyimpan index awal footer bila ada
    beginUl = 0 # untuk menyimpan index pertama dari ul
    endUl = len(response) # untuk menyimpan index terakhir dari message, index terakhir
    li = 0
    # untuk mencari li dan indexnya
    for i in range(1,jumlah+1): # sejumlah ul yang ada di response, untuk li
        beginUl = response.find("[ul]",beginUl, endUl) # beginUl diawali dari @? untuk tiap ul
        end = response.find("[/ul]",beginUl, endUl) # end untuk index terakhir di ul yang terkait (1 ul dengan ^)
        begin = beginUl+1 # begin untuk menyimpan index pertama untuk pencarian li, sebagai temp
        li = 0 # jumlah li yang ada diinisialisasi dengan nilai 0
        while response.find("[li]",begin, endUl) < end-2 and response.find("[li]",begin, endUl) != -1: # mencari li sampai dengan li ada di sebelum penutup ul
            # untuk tiap li ada di ul bersangkutan
            indexLi[i-1].append(response.find("[li]",begin, endUl)+4) # menambah index awal dari tiap li
            li = li + 1 # jumlah li ditambah sesuai li yang ada
            begin = response.find("[/li]",begin, endUl) + 3 # mengubah index temp untuk mencari li selanjutnya
        # menyimpan jumlah li yang ada di tiap ul
        objJson = objJson + ', {"'+str(i)+'": '+str(li) + "}"
        jumlahLi.append(li)
        beginUl = end + 4 # mengubah beginUl menjadi index ul selanjutnya bila ada
    beginUl = 0 # untuk menyimpan index pertama dari ul
    endUl = len(response) # untuk menyimpan index terakhir dari message, index terakhir
    objJson = objJson + '], "footer": [{ "0": 0 }'
    for i in range(1,jumlah+1): # sejumlah ul yang ada di response, untuk footer
        beginUl = response.find("[ul]",beginUl, endUl) # beginUl diawali dari @? untuk tiap ul
        end = response.find("[/ul]",beginUl, endUl) # end untuk index terakhir di ul yang terkait (1 ul dengan ^)
        objJson = objJson + ', {"'+str(i)+'": ' # pembuka footer per ul
        if response.find("[footer]", beginUl, end) != -1: # ada footer
            jumlahFooter.append(1)
            indexFooter.append(response.find("[footer]", beginUl, end) + 8)
            objJson = objJson + '1'
        else: # tidak ada footer
            jumlahFooter.append(0)
            indexFooter.append(0)
            objJson = objJson + '0'
        objJson = objJson + "}" # penutup footer per ul
        beginUl = end
    # menyimpan message dari response
    end = len(response) # temp untuk menyimpan akhir range dari message yang akan disimpan
    objJson = objJson + ' ], "message": [ {"0": "' # penutup ul li dan pembuka message yang akan disimpan
    # untuk menyimpan message awal
    if jumlah == 0: # untuk menyimpan message bila tidak ada bulleting
        objJson = objJson + response # langsung menyimpan semua response yang ada
    elif jumlah != 1: # untuk menyimpan message awal sebelum masuk ke bulleting
        end = response.find("[enter]") # untuk menyimpan index terakhir dari message
        objJson = objJson + response[0:end]
    # untuk menutup message awal
    objJson = objJson + '"}'
    begin = end+7 # temp untuk menyimpan awal ul
    #masukkan ke message
    for i in range(1, jumlah+1): # untuk tiap ul yang ada
        end = len(response) # penanda penutup ul
        objJson = objJson + ', {"'+str(i)+'": [ {"0": "' # untuk membuka message untuk ul ke i
        #message '0' judul ul
        if(jumlah == 1):
            begin = 0
        end = response.find("[ul]",begin, end)-1 # index pembuka message di start ul
        objJson = objJson + response[begin:end] + '"}' # menyimpan message awal ul
        # menyimpan message di tiap li
        for j in range(1, jumlahLi[i-1] + 1): # sebanyak li yang ada
            begin = indexLi[i-1][j-1] # index awal berdasarkan yang telah disimpan
            end = response.find("[/li]",begin,len(response)) # -@ penanda li berhenti
            objJson = objJson + ', {"'+str(j)+'": "' + response[begin:end] + '"} ' # menyimpan message tiap li
        begin = response.find("[/ul]",begin, len(response)) + 6 # diperbarui untuk ul selanjutnya bila ada
        objJson = objJson + ']}' # penutup li di ul
    # menyimpan message footer dari response
    end = len(response) # temp untuk menyimpan akhir range dari message yang akan disimpan
    objJson = objJson + ' ], "m_footer": [ {"0": "' # penutup ul li dan pembuka message yang akan disimpan
    # untuk menutup message awal
    if jumlah == 0: # tutup message tidak ada ul, berarti tutup message
        objJson = objJson + '"}]'
    else: # message belum ditutup, masih ada message dari li
        objJson = objJson + '"}'
    begin = response.find("[ul]",0, len(response)) # temp untuk menyimpan awal ul
    #masukkan ke message ke m_footer
    for i in range(1, jumlah+1): # untuk tiap ul yang ada
        begin = indexFooter[i-1] # penanda pembuka ul
        end =  response.find("[/footer]",begin, len(response)) # penanda penutup ul
        objJson = objJson + ', {"'+str(i)+'": "'
        if jumlahFooter[i-1] != 0:
            objJson = objJson + response[begin:end]
        objJson = objJson + '"} '
    # menutup message yang akan dikembalikan
    if jumlah == 0: # tutup message bila tidak ada bulleting
        objJson = objJson + '}'
    else: # tutup message bila ada bulleting
        objJson = objJson + ']}'
    # Mengembalikan message
    return objJson

# Function Main
@app.route("/<query>")
def index(query):
    global email
    global isemail
    # query = input user
    query = query.lower()

    if  query.count('@') > 0 :
        lst = re.findall('\S+@\S+',query)
        email =  "".join(lst)
        isemail = True
        
    
    #Stopword Removal
    stopwords = ['ada', 'adalah', 'adanya', 'adapun', 'agak', 'agaknya', 'agar', 'akan', 'akankah', 'akhir', 'akhiri', 'akhirnya', 'aku', 'akulah', 'amat', 'amatlah', 'anda', 'andalah', 'antar', 'antara', 'antaranya', 'apa', 'apaan', 'apabila', 'apakah', 'apalagi', 'apatah', 'artinya', 'asal', 'asalkan', 'atas', 'atau', 'ataukah', 'ataupun', 'awal', 'awalnya', 'bagai', 'bagaikan', 'bagaimana', 'bagaimanakah', 'bagaimanapun', 'bagi', 'bagian', 'bahkan', 'bahwa', 'bahwasanya', 'baik', 'bakal', 'bakalan', 'balik', 'banyak', 'bapak', 'baru', 'bawah', 'beberapa', 'begini', 'beginian', 'beginikah', 'beginilah', 'begitu', 'begitukah', 'begitulah', 'begitupun', 'bekerja', 'belakang', 'belakangan', 'belum', 'belumlah', 'benar', 'benarkah', 'benarlah', 'berada', 'berakhir', 'berakhirlah', 'berakhirnya', 'berapa', 'berapakah', 'berapalah', 'berapapun', 'berarti', 'berawal', 'berbagai', 'berdatangan', 'beri', 'berikan', 'berikut', 'berikutnya', 'berjumlah', 'berkali-kali', 'berkata', 'berkehendak', 'berkeinginan', 'berkenaan', 'berlainan', 'berlalu', 'berlangsung', 'berlebihan', 'bermacam', 'bermacam-macam', 'bermaksud', 'bermula', 'bersama', 'bersama-sama', 'bersiap', 'bersiap-siap', 'bertanya', 'bertanya-tanya', 'berturut', 'berturut-turut', 'bertutur', 'berujar', 'berupa', 'besar', 'betul', 'betulkah', 'biasa', 'biasanya', 'bila', 'bilakah', 'bisa', 'bisakah', 'boleh', 'bolehkah', 'bolehlah', 'buat', 'bukan', 'bukankah', 'bukanlah', 'bukannya', 'bulan', 'bung', 'cara', 'caranya', 'cukup', 'cukupkah', 'cukuplah', 'cuma', 'dahulu', 'dalam', 'dan', 'dapat', 'dari', 'daripada', 'datang', 'dekat', 'demi', 'demikian', 'demikianlah', 'dengan', 'depan', 'di', 'dia', 'diakhiri', 'diakhirinya', 'dialah', 'diantara', 'diantaranya', 'diberi', 'diberikan', 'diberikannya', 'dibuat', 'dibuatnya', 'didapat', 'didatangkan', 'digunakan', 'diibaratkan', 'diibaratkannya', 'diingat', 'diingatkan', 'diinginkan', 'dijawab', 'dijelaskan', 'dijelaskannya', 'dikarenakan', 'dikatakan', 'dikatakannya', 'dikerjakan', 'diketahui', 'diketahuinya', 'dikira', 'dilakukan', 'dilalui', 'dilihat', 'dimaksud', 'dimaksudkan', 'dimaksudkannya', 'dimaksudnya', 'diminta', 'dimintai', 'dimisalkan', 'dimulai', 'dimulailah', 'dimulainya', 'dimungkinkan', 'dini', 'dipastikan', 'diperbuat', 'diperbuatnya', 'dipergunakan', 'diperkirakan', 'diperlihatkan', 'diperlukan', 'diperlukannya', 'dipersoalkan', 'dipertanyakan', 'dipunyai', 'diri', 'dirinya', 'disampaikan', 'disebut', 'disebutkan', 'disebutkannya', 'disini', 'disinilah', 'ditambahkan', 'ditandaskan', 'ditanya', 'ditanyai', 'ditanyakan', 'ditegaskan', 'ditujukan', 'ditunjuk', 'ditunjuki', 'ditunjukkan', 'ditunjukkannya', 'ditunjuknya', 'dituturkan', 'dituturkannya', 'diucapkan', 'diucapkannya', 'diungkapkan', 'dong', 'dua', 'dulu', 'empat', 'enggak', 'enggaknya', 'entah', 'entahlah', 'guna', 'gunakan', 'gimana', 'hal', 'hampir', 'hanya', 'hanyalah', 'hari', 'harus', 'haruslah', 'harusnya', 'hendak', 'hendaklah', 'hendaknya', 'hingga', 'ia', 'ialah', 'ibarat', 'ibaratkan', 'ibaratnya', 'ibu', 'ikut', 'ingat', 'ingat-ingat', 'ingin', 'inginkah', 'inginkan', 'ini', 'inikah', 'inilah', 'itu', 'itukah', 'itulah', 'jadi', 'jadilah', 'jadinya', 'jangan', 'jangankan', 'janganlah', 'jauh', 'jawab', 'jawaban', 'jawabnya', 'jelas', 'jelaskan', 'jelaslah', 'jelasnya', 'jika', 'jikalau', 'juga', 'jumlah', 'jumlahnya', 'justru', 'kala', 'kalau', 'kalaulah', 'kalaupun', 'kalian', 'kami', 'kamilah', 'kamu', 'kamulah', 'kan', 'kapan', 'kapankah', 'kapanpun', 'karena', 'karenanya', 'kasus', 'kata', 'katakan', 'katakanlah', 'katanya', 'ke', 'keadaan', 'kebetulan', 'kecil', 'kedua', 'keduanya', 'keinginan', 'kelamaan', 'kelihatan', 'kelihatannya', 'kelima', 'keluar', 'kembali', 'kemudian', 'kemungkinan', 'kemungkinannya', 'kenapa', 'kepada', 'kepadanya', 'kesampaian', 'keseluruhan', 'keseluruhannya', 'keterlaluan', 'ketika', 'khususnya', 'kini', 'kinilah', 'kira', 'kira-kira', 'kiranya', 'kita', 'kitalah', 'kok', 'kurang', 'lagi', 'lagian', 'lah', 'lain', 'lainnya', 'lalu', 'lama', 'lamanya', 'lanjut', 'lanjutnya', 'lebih', 'lewat', 'lima', 'luar', 'macam', 'maka', 'makanya', 'makin', 'malah', 'malahan', 'mampu', 'mampukah', 'mana', 'manakala', 'manalagi', 'masa', 'masalah', 'masalahnya', 'masih', 'masihkah', 'masing', 'masing-masing', 'mau', 'maupun', 'melainkan', 'melakukan', 'melalui', 'melihat', 'melihatnya', 'memang', 'memastikan', 'memberi', 'memberikan', 'membuat', 'memerlukan', 'memihak', 'meminta', 'memintakan', 'memisalkan', 'memperbuat', 'mempergunakan', 'memperkirakan', 'memperlihatkan', 'mempersiapkan', 'mempersoalkan', 'mempertanyakan', 'mempunyai', 'memulai', 'memungkinkan', 'menaiki', 'menambahkan', 'menandaskan', 'menanti', 'menanti-nanti', 'menantikan', 'menanya', 'menanyai', 'menanyakan', 'mendapat', 'mendapatkan', 'mendatang', 'mendatangi', 'mendatangkan', 'menegaskan', 'mengakhiri', 'mengapa', 'mengatakan', 'mengatakannya', 'mengenai', 'mengerjakan', 'mengetahui', 'menggunakan', 'menghendaki', 'mengibaratkan', 'mengibaratkannya', 'mengingat', 'mengingatkan', 'menginginkan', 'mengira', 'mengucapkan', 'mengucapkannya', 'mengungkapkan', 'menjadi', 'menjawab', 'menjelaskan', 'menuju', 'menunjuk', 'menunjuki', 'menunjukkan', 'menunjuknya', 'menurut', 'menuturkan', 'menyampaikan', 'menyangkut', 'menyatakan', 'menyebutkan', 'menyeluruh', 'menyiapkan', 'merasa', 'mereka', 'merekalah', 'merupakan', 'meski', 'meskipun', 'meyakini', 'meyakinkan', 'minta', 'mirip', 'misal', 'misalkan', 'misalnya', 'mula', 'mulai', 'mulailah', 'mulanya', 'mungkin', 'mungkinkah', 'nah', 'naik', 'namun', 'nanti', 'nantinya', 'nyaris', 'nyatanya', 'oleh', 'olehnya', 'pada', 'padahal', 'padanya', 'pak', 'paling', 'panjang', 'pantas', 'para', 'pasti', 'pastilah', 'penting', 'pentingnya', 'per', 'percuma', 'perlu', 'perlukah', 'perlunya', 'pernah', 'persoalan', 'pertama', 'pertama-tama', 'pertanyaan', 'pertanyakan', 'pihak', 'pihaknya', 'pukul', 'pula', 'pun', 'punya', 'rasa', 'rasanya', 'rata', 'rupanya', 'saat', 'saatnya', 'saja', 'sajalah', 'saling', 'sama', 'sama-sama', 'sambil', 'sampai', 'sampai-sampai', 'sampaikan', 'sana', 'sangat', 'sangatlah', 'satu', 'saya', 'sayalah', 'se', 'sebab', 'sebabnya', 'sebagai', 'sebagaimana', 'sebagainya', 'sebagian', 'sebaik', 'sebaik-baiknya', 'sebaiknya', 'sebaliknya', 'sebanyak', 'sebegini', 'sebegitu', 'sebelum', 'sebelumnya', 'sebenarnya', 'seberapa', 'sebesar', 'sebetulnya', 'sebisanya', 'sebuah', 'sebut', 'sebutlah', 'sebutnya', 'secara', 'secukupnya', 'sedang', 'sedangkan', 'sedemikian', 'sedikit', 'sedikitnya', 'seenaknya', 'segala', 'segalanya', 'segera', 'seharusnya', 'sehingga', 'seingat', 'sejak', 'sejauh', 'sejenak', 'sejumlah', 'sekadar', 'sekadarnya', 'sekali', 'sekali-kali', 'sekalian', 'sekaligus', 'sekalipun', 'sekarang', 'sekarang', 'sekecil', 'seketika', 'sekiranya', 'sekitar', 'sekitarnya', 'sekurang-kurangnya', 'sekurangnya', 'sela', 'selain', 'selaku', 'selalu', 'selama', 'selama-lamanya', 'selamanya', 'selanjutnya', 'seluruh', 'seluruhnya', 'semacam', 'semakin', 'semampu', 'semampunya', 'semasa', 'semasih', 'semata', 'semata-mata', 'semaunya', 'sementara', 'semisal', 'semisalnya', 'sempat', 'semua', 'semuanya', 'semula', 'sendiri', 'sendirian', 'sendirinya', 'seolah', 'seolah-olah', 'seorang', 'sepanjang', 'sepantasnya', 'sepantasnyalah', 'seperlunya', 'seperti', 'sepertinya', 'sepihak', 'sering', 'seringnya', 'serta', 'serupa', 'sesaat', 'sesama', 'sesampai', 'sesegera', 'sesekali', 'seseorang', 'sesuatu', 'sesuatunya', 'sesudah', 'sesudahnya', 'setelah', 'setempat', 'setengah', 'seterusnya', 'setiap', 'setiba', 'setibanya', 'setidak-tidaknya', 'setidaknya', 'setinggi', 'seusai', 'sewaktu', 'siap', 'siapa', 'siapakah', 'siapapun', 'sini', 'sinilah', 'soal', 'soalnya', 'suatu', 'sudah', 'sudahkah', 'sudahlah', 'supaya', 'tadi', 'tadinya', 'tahu', 'tahun', 'tak', 'tambah', 'tambahnya', 'tampak', 'tampaknya', 'tandas', 'tandasnya', 'tanpa', 'tanya', 'tanyakan', 'tanyanya', 'tapi', 'tegas', 'tegasnya', 'telah', 'tempat', 'tengah', 'tentang', 'tentu', 'tentulah', 'tentunya', 'tepat', 'terakhir', 'terasa', 'terbanyak', 'terdahulu', 'terdapat', 'terdiri', 'terhadap', 'terhadapnya', 'teringat', 'teringat-ingat', 'terjadi', 'terjadilah', 'terjadinya', 'terkira', 'terlalu', 'terlebih', 'terlihat', 'termasuk', 'ternyata', 'tersampaikan', 'tersebut', 'tersebutlah', 'tertentu', 'tertuju', 'terus', 'terutama', 'tetap', 'tetapi', 'tiap', 'tiba', 'tiba-tiba', 'tidak', 'tidakkah', 'tidaklah', 'tiga', 'tinggi', 'toh', 'tunjuk', 'turut', 'tutur', 'tuturnya', 'ucap', 'ucapnya', 'ujar', 'ujarnya', 'umum', 'umumnya', 'ungkap', 'ungkapnya', 'untuk', 'usah', 'usai', 'waduh', 'wah', 'wahai', 'waktu', 'waktunya', 'walau', 'walaupun', 'wong', 'yaitu', 'yakin', 'yakni', 'yang']
    listed  = query.split()
    query_list = [e for e in listed if e not in stopwords]
    query = ' '.join(query_list)
    
    #Stemming
    stemFactory = StemmerFactory()
    stemmer = stemFactory.create_stemmer()
    query = stemmer.stem(query)

    if not query:
        query = "THIS IS AN EMPTY QUERY"
        
    if query.isdigit() and len(query) > 5 :
        query = "THE PHONE NUMBER IS " + query
    
    

    if isemail :
        query = "THE EMAIL ADDRESS IS " + email
        
    
    
    # Meminta hasil response dari query berdasarkan AIML
    response = kernel.respond(query)
    # Menentukan jenis message yang akan dikembalikan
    if cekQuery(response):
        sedia = response.lower()
        sedia = sedia.replace(" ","")
        # print(sedia)
        return messageAvailability(sedia)
    else:
        return messageChat(response)

if __name__ == '__main__':
    app.run(debug=True)
