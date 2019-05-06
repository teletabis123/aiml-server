<ul> -> @? -> [ul]
</ul> -> ?@ -> [/ul]
<li> -> @- -> [li]
</li> -> -@ -> [/li]
\n -> @^ -> [enter]
footer -> [footer]
/footer -> [/footer]
@@ -> [request]

{
	"ul": 3,
	"il": [{
		"0": 1
	}, {
		"1": 2
	}, {
		"2": 2
	}, {
		"3": 2
	}],
    "footer": [{
		"0": 0
	}, {
		"1": 1
	}, {
		"2": 1
	}, {
		"3": 1
	}],
	"message": [{
		"0": "Informasi mengenai Check in / Check Out:"
	}, {
		"1": [{
			"0": "ter] Informasi Umum:"
		}, {
			"1": "Jam Check In jam 2 siang dan Check Out jam 12 siang. Diberikan toleransi 1/2 jam."
		}, {
			"2": "Untuk Check Out akan ditelpon jam 10 untuk diingatkan."
		}]
	}, {
		"2": [{
			"0": "Early Check In"
		}, {
			"1": "Sampai sebelum jam 8 pagi, ditambah 50% dari biaya kamar."
		}, {
			"2": "Dari jam 9 pagi sampai dengan jam Check Out Normal, ditambah 25% dari biaya kamar."
		}]
	}, {
		"3": [{
			"0": "Late Check Out"
		}, {
			"1": "Dari jam Check Out Normal sampai jam 6 sore, ditambah 50% dari biaya kamar."
		}, {
			"2": "Jam Check Out setelah jam 6 sore, ditambah 100% dari biaya kamar."
		}]
	}],
	"m_footer": [{
		"0": ""
	}, {
		"1": "Message footer 1"
	}, {
        "2": "Message footer 2"
    }]
}

{
	"ul": 1,
	"il": [{
		"0": 1
	}, {
		"1": 10
	}],
	"message": [{
		"0": ""
	}, {
		"1": [{
			"0": "Halo, Saya Chatbot yang akan membantu Anda menjelajahi informasi dan reservasi tentang:"
		}, {
			"1": "Tentang Santika Premiere Slipi"
		}, {
			"2": "Kamar Hotel"
		}, {
			"3": "Cek Ketersediaan Kamar"
		}, {
			"4": "Mengenai Reservasi"
		}, {
			"5": "Mengenai Pembayaran"
		}, {
			"6": "Acara Pernikahan"
		}, {
			"7": "Ruangan Rapat"
		}, {
			"8": "Transportasi"
		}, {
			"9": "Restoran"
		}, {
			"10": "Fasilitas Lain."
		}]
	}],
	"m_footer": [{
		"0": ""
	}, {
		"1": "Message footer"
	}]
}

{
	"ul": 0,
	"il": [{
		"0": 1
	}],
    "footer": [{
		"0": 0
	}],
	"message": [{
		"0": "Maaf, informasi mengenai asdf belum tersedia. Silahkan menghubungi front office Santika Hotel Premiere untuk informasi lebih lanjut."
	}],
	"m_footer": [{
		"0": ""
	}]
}



Ketersediaan:
- jenis kamar, tanggal check in, berapa malam, berapa kamar
<sedia = kamar> Kamar * <srai> *
<di tiap jenis> <condition sedia=kamar> <think set kamar=> <think set sedia=tanggal> <srai> TANGGAL
<di TANGGAL> <condition sedia=tanggal> <think set tanggal=> <think set sedia=malam> <srai> MALAM
<di MALAM> <condition sedia=malam> <think set malam=> <think set sedia=banyak> <srai> KAMAR
<di BANYAK> <condition sedia=banyak> <think set banyak=> <srai> [request]

<condition name = "sedia" value = "kamar">
                
            </condition>

[request]kamardeluxetanggal12desember2019malam3malambanyak3kamar