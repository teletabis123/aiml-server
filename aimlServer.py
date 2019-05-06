import os
import aiml
import json
import requests
import datetime
from flask import Flask
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory


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
    if response.find("[request]",0,len(response)) != -1:
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
    
    dateNow = datetime.datetime.now()
    
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
        if(not(tanggal.isdigit() and bulan.isdigit() and tahun.isdigit()) or not(len(tanggal)==2 and len(bulan)==2 and len(tahun)==4)):
            return False
        if int(tahun) < dateNow.year:
            return False
        elif int(bulan) < dateNow.month:
            return False
        elif int(tanggal) < dateNow.day:
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
    message = '{"ul": 0, "li": [ {"0": 1} ], "footer": [ {"0": 0} ], "message": [ {"0": "'
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
        message = message + 'Kamar ' + kamar + ' yang tersedia pada tanggal ' + tanggal + '-' + bulan + '-' + tahun
        message = message + ' adalah ' + str(king) + ' kamar King Size'
        if twin != -1:
            message = message + ' dan ' + str(twin) + ' kamar Twin Size'
    else: # bila input salah
        if jenis == 0:
            message = message + 'Format pengecekkan kamar salah'
        else:
            message = message + 'Format tanggal yang anda masukkan salah'
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
    begin = end+3 # temp untuk menyimpan awal ul
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
    # query = input user
    query = query.lower()
    
    #Stopword Remvoal
    stopwords = ['ada', 'adalah', 'adanya', 'adapun', 'agak', 'agaknya', 'agar', 'akan', 'akankah', 'akhir', 'akhiri', 'akhirnya', 'aku', 'akulah', 'amat', 'amatlah', 'anda', 'andalah', 'antar', 'antara', 'antaranya', 'apa', 'apaan', 'apabila', 'apakah', 'apalagi', 'apatah', 'artinya', 'asal', 'asalkan', 'atas', 'atau', 'ataukah', 'ataupun', 'awal', 'awalnya', 'bagai', 'bagaikan', 'bagaimana', 'bagaimanakah', 'bagaimanapun', 'bagi', 'bagian', 'bahkan', 'bahwa', 'bahwasanya', 'baik', 'bakal', 'bakalan', 'balik', 'banyak', 'bapak', 'baru', 'bawah', 'beberapa', 'begini', 'beginian', 'beginikah', 'beginilah', 'begitu', 'begitukah', 'begitulah', 'begitupun', 'bekerja', 'belakang', 'belakangan', 'belum', 'belumlah', 'benar', 'benarkah', 'benarlah', 'berada', 'berakhir', 'berakhirlah', 'berakhirnya', 'berapa', 'berapakah', 'berapalah', 'berapapun', 'berarti', 'berawal', 'berbagai', 'berdatangan', 'beri', 'berikan', 'berikut', 'berikutnya', 'berjumlah', 'berkali-kali', 'berkata', 'berkehendak', 'berkeinginan', 'berkenaan', 'berlainan', 'berlalu', 'berlangsung', 'berlebihan', 'bermacam', 'bermacam-macam', 'bermaksud', 'bermula', 'bersama', 'bersama-sama', 'bersiap', 'bersiap-siap', 'bertanya', 'bertanya-tanya', 'berturut', 'berturut-turut', 'bertutur', 'berujar', 'berupa', 'besar', 'betul', 'betulkah', 'biasa', 'biasanya', 'bila', 'bilakah', 'bisa', 'bisakah', 'boleh', 'bolehkah', 'bolehlah', 'buat', 'bukan', 'bukankah', 'bukanlah', 'bukannya', 'bulan', 'bung', 'cara', 'caranya', 'cukup', 'cukupkah', 'cukuplah', 'cuma', 'dahulu', 'dalam', 'dan', 'dapat', 'dari', 'daripada', 'datang', 'dekat', 'demi', 'demikian', 'demikianlah', 'dengan', 'depan', 'di', 'dia', 'diakhiri', 'diakhirinya', 'dialah', 'diantara', 'diantaranya', 'diberi', 'diberikan', 'diberikannya', 'dibuat', 'dibuatnya', 'didapat', 'didatangkan', 'digunakan', 'diibaratkan', 'diibaratkannya', 'diingat', 'diingatkan', 'diinginkan', 'dijawab', 'dijelaskan', 'dijelaskannya', 'dikarenakan', 'dikatakan', 'dikatakannya', 'dikerjakan', 'diketahui', 'diketahuinya', 'dikira', 'dilakukan', 'dilalui', 'dilihat', 'dimaksud', 'dimaksudkan', 'dimaksudkannya', 'dimaksudnya', 'diminta', 'dimintai', 'dimisalkan', 'dimulai', 'dimulailah', 'dimulainya', 'dimungkinkan', 'dini', 'dipastikan', 'diperbuat', 'diperbuatnya', 'dipergunakan', 'diperkirakan', 'diperlihatkan', 'diperlukan', 'diperlukannya', 'dipersoalkan', 'dipertanyakan', 'dipunyai', 'diri', 'dirinya', 'disampaikan', 'disebut', 'disebutkan', 'disebutkannya', 'disini', 'disinilah', 'ditambahkan', 'ditandaskan', 'ditanya', 'ditanyai', 'ditanyakan', 'ditegaskan', 'ditujukan', 'ditunjuk', 'ditunjuki', 'ditunjukkan', 'ditunjukkannya', 'ditunjuknya', 'dituturkan', 'dituturkannya', 'diucapkan', 'diucapkannya', 'diungkapkan', 'dong', 'dua', 'dulu', 'empat', 'enggak', 'enggaknya', 'entah', 'entahlah', 'guna', 'gunakan', 'hal', 'hampir', 'hanya', 'hanyalah', 'hari', 'harus', 'haruslah', 'harusnya', 'hendak', 'hendaklah', 'hendaknya', 'hingga', 'ia', 'ialah', 'ibarat', 'ibaratkan', 'ibaratnya', 'ibu', 'ikut', 'ingat', 'ingat-ingat', 'ingin', 'inginkah', 'inginkan', 'ini', 'inikah', 'inilah', 'itu', 'itukah', 'itulah', 'jadi', 'jadilah', 'jadinya', 'jangan', 'jangankan', 'janganlah', 'jauh', 'jawab', 'jawaban', 'jawabnya', 'jelas', 'jelaskan', 'jelaslah', 'jelasnya', 'jika', 'jikalau', 'juga', 'jumlah', 'jumlahnya', 'justru', 'kala', 'kalau', 'kalaulah', 'kalaupun', 'kalian', 'kami', 'kamilah', 'kamu', 'kamulah', 'kan', 'kapan', 'kapankah', 'kapanpun', 'karena', 'karenanya', 'kasus', 'kata', 'katakan', 'katakanlah', 'katanya', 'ke', 'keadaan', 'kebetulan', 'kecil', 'kedua', 'keduanya', 'keinginan', 'kelamaan', 'kelihatan', 'kelihatannya', 'kelima', 'keluar', 'kembali', 'kemudian', 'kemungkinan', 'kemungkinannya', 'kenapa', 'kepada', 'kepadanya', 'kesampaian', 'keseluruhan', 'keseluruhannya', 'keterlaluan', 'ketika', 'khususnya', 'kini', 'kinilah', 'kira', 'kira-kira', 'kiranya', 'kita', 'kitalah', 'kok', 'kurang', 'lagi', 'lagian', 'lah', 'lain', 'lainnya', 'lalu', 'lama', 'lamanya', 'lanjut', 'lanjutnya', 'lebih', 'lewat', 'lima', 'luar', 'macam', 'maka', 'makanya', 'makin', 'malah', 'malahan', 'mampu', 'mampukah', 'mana', 'manakala', 'manalagi', 'masa', 'masalah', 'masalahnya', 'masih', 'masihkah', 'masing', 'masing-masing', 'mau', 'maupun', 'melainkan', 'melakukan', 'melalui', 'melihat', 'melihatnya', 'memang', 'memastikan', 'memberi', 'memberikan', 'membuat', 'memerlukan', 'memihak', 'meminta', 'memintakan', 'memisalkan', 'memperbuat', 'mempergunakan', 'memperkirakan', 'memperlihatkan', 'mempersiapkan', 'mempersoalkan', 'mempertanyakan', 'mempunyai', 'memulai', 'memungkinkan', 'menaiki', 'menambahkan', 'menandaskan', 'menanti', 'menanti-nanti', 'menantikan', 'menanya', 'menanyai', 'menanyakan', 'mendapat', 'mendapatkan', 'mendatang', 'mendatangi', 'mendatangkan', 'menegaskan', 'mengakhiri', 'mengapa', 'mengatakan', 'mengatakannya', 'mengenai', 'mengerjakan', 'mengetahui', 'menggunakan', 'menghendaki', 'mengibaratkan', 'mengibaratkannya', 'mengingat', 'mengingatkan', 'menginginkan', 'mengira', 'mengucapkan', 'mengucapkannya', 'mengungkapkan', 'menjadi', 'menjawab', 'menjelaskan', 'menuju', 'menunjuk', 'menunjuki', 'menunjukkan', 'menunjuknya', 'menurut', 'menuturkan', 'menyampaikan', 'menyangkut', 'menyatakan', 'menyebutkan', 'menyeluruh', 'menyiapkan', 'merasa', 'mereka', 'merekalah', 'merupakan', 'meski', 'meskipun', 'meyakini', 'meyakinkan', 'minta', 'mirip', 'misal', 'misalkan', 'misalnya', 'mula', 'mulai', 'mulailah', 'mulanya', 'mungkin', 'mungkinkah', 'nah', 'naik', 'namun', 'nanti', 'nantinya', 'nyaris', 'nyatanya', 'oleh', 'olehnya', 'pada', 'padahal', 'padanya', 'pak', 'paling', 'panjang', 'pantas', 'para', 'pasti', 'pastilah', 'penting', 'pentingnya', 'per', 'percuma', 'perlu', 'perlukah', 'perlunya', 'pernah', 'persoalan', 'pertama', 'pertama-tama', 'pertanyaan', 'pertanyakan', 'pihak', 'pihaknya', 'pukul', 'pula', 'pun', 'punya', 'rasa', 'rasanya', 'rata', 'rupanya', 'saat', 'saatnya', 'saja', 'sajalah', 'saling', 'sama', 'sama-sama', 'sambil', 'sampai', 'sampai-sampai', 'sampaikan', 'sana', 'sangat', 'sangatlah', 'satu', 'saya', 'sayalah', 'se', 'sebab', 'sebabnya', 'sebagai', 'sebagaimana', 'sebagainya', 'sebagian', 'sebaik', 'sebaik-baiknya', 'sebaiknya', 'sebaliknya', 'sebanyak', 'sebegini', 'sebegitu', 'sebelum', 'sebelumnya', 'sebenarnya', 'seberapa', 'sebesar', 'sebetulnya', 'sebisanya', 'sebuah', 'sebut', 'sebutlah', 'sebutnya', 'secara', 'secukupnya', 'sedang', 'sedangkan', 'sedemikian', 'sedikit', 'sedikitnya', 'seenaknya', 'segala', 'segalanya', 'segera', 'seharusnya', 'sehingga', 'seingat', 'sejak', 'sejauh', 'sejenak', 'sejumlah', 'sekadar', 'sekadarnya', 'sekali', 'sekali-kali', 'sekalian', 'sekaligus', 'sekalipun', 'sekarang', 'sekarang', 'sekecil', 'seketika', 'sekiranya', 'sekitar', 'sekitarnya', 'sekurang-kurangnya', 'sekurangnya', 'sela', 'selain', 'selaku', 'selalu', 'selama', 'selama-lamanya', 'selamanya', 'selanjutnya', 'seluruh', 'seluruhnya', 'semacam', 'semakin', 'semampu', 'semampunya', 'semasa', 'semasih', 'semata', 'semata-mata', 'semaunya', 'sementara', 'semisal', 'semisalnya', 'sempat', 'semua', 'semuanya', 'semula', 'sendiri', 'sendirian', 'sendirinya', 'seolah', 'seolah-olah', 'seorang', 'sepanjang', 'sepantasnya', 'sepantasnyalah', 'seperlunya', 'seperti', 'sepertinya', 'sepihak', 'sering', 'seringnya', 'serta', 'serupa', 'sesaat', 'sesama', 'sesampai', 'sesegera', 'sesekali', 'seseorang', 'sesuatu', 'sesuatunya', 'sesudah', 'sesudahnya', 'setelah', 'setempat', 'setengah', 'seterusnya', 'setiap', 'setiba', 'setibanya', 'setidak-tidaknya', 'setidaknya', 'setinggi', 'seusai', 'sewaktu', 'siap', 'siapa', 'siapakah', 'siapapun', 'sini', 'sinilah', 'soal', 'soalnya', 'suatu', 'sudah', 'sudahkah', 'sudahlah', 'supaya', 'tadi', 'tadinya', 'tahu', 'tahun', 'tak', 'tambah', 'tambahnya', 'tampak', 'tampaknya', 'tandas', 'tandasnya', 'tanpa', 'tanya', 'tanyakan', 'tanyanya', 'tapi', 'tegas', 'tegasnya', 'telah', 'tempat', 'tengah', 'tentang', 'tentu', 'tentulah', 'tentunya', 'tepat', 'terakhir', 'terasa', 'terbanyak', 'terdahulu', 'terdapat', 'terdiri', 'terhadap', 'terhadapnya', 'teringat', 'teringat-ingat', 'terjadi', 'terjadilah', 'terjadinya', 'terkira', 'terlalu', 'terlebih', 'terlihat', 'termasuk', 'ternyata', 'tersampaikan', 'tersebut', 'tersebutlah', 'tertentu', 'tertuju', 'terus', 'terutama', 'tetap', 'tetapi', 'tiap', 'tiba', 'tiba-tiba', 'tidak', 'tidakkah', 'tidaklah', 'tiga', 'tinggi', 'toh', 'tunjuk', 'turut', 'tutur', 'tuturnya', 'ucap', 'ucapnya', 'ujar', 'ujarnya', 'umum', 'umumnya', 'ungkap', 'ungkapnya', 'untuk', 'usah', 'usai', 'waduh', 'wah', 'wahai', 'waktu', 'waktunya', 'walau', 'walaupun', 'wong', 'yaitu', 'yakin', 'yakni', 'yang']
    
    listed  = query.split()
    query = [e for e in listed if e not in stopwords]
    
    #Stemming
    stemFactory = StemmerFactory()
    stemmer = stemFactory.create_stemmer()
    query = stemmer.stem(query)
    
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
