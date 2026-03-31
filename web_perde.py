from flask import Flask, request, render_template_string, session, redirect, url_for
import RPi.GPIO as GPIO
import time
import threading
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_gizli_anahtar_123" 

# ================= KULLANICI & SİSTEM AYARLARI =================
GIRIS_ID = "1234"        
HEDEF_TUR = 37           
MOTOR_HIZI = 0.0005      
ADIM_PER_TUR = 1600      
ESIK_DEGERI = 550        
TEPKIME_SINIRI = 30      

# ================= PİN AYARLARI (BCM MODU) =================
LDR_PIN = 3    
DIR_PIN = 21   
STEP_PIN = 20  
ENA_PIN = 16   

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)
GPIO.setup(ENA_PIN, GPIO.OUT)
GPIO.output(ENA_PIN, GPIO.HIGH) 

# ================= GLOBAL DEĞİŞKENLER =================
PERDE_DURUMU = "acik"    
SISTEM_MODU = "otomatik" 
MOTOR_MESGUL = False     
DURDUR_ISTEGI = False    
ANLIK_ISIK = 0           
SISTEM_LOGLARI = ["Sistem Başlatıldı. Motor Uykuda."]

def log_ekle(mesaj):
    saat = datetime.now().strftime("%H:%M:%S")
    SISTEM_LOGLARI.insert(0, f"[{saat}] {mesaj}")
    if len(SISTEM_LOGLARI) > 5:
        SISTEM_LOGLARI.pop()

# ================= WEB ARAYÜZÜ TASARIMI =================
HTML_SAYFASI = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Akıllı Perde Kontrol Paneli</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #e9ecef; text-align: center; padding: 10px; margin: 0; }
        .kutu { background: white; padding: 20px; border-radius: 12px; box-shadow: 0px 4px 15px rgba(0,0,0,0.1); max-width: 450px; margin: auto; }
        .btn { display: inline-block; padding: 15px 25px; margin: 5px; font-size: 16px; color: white; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; font-weight: bold; }
        .btn-ac { background-color: #28a745; width: 40%; }
        .btn-kapat { background-color: #007bff; width: 40%; }
        .btn-durdur { background-color: #dc3545; width: 90%; padding: 20px; font-size: 20px; animation: yanipsonme 1s infinite; }
        .btn-oto { background-color: #6c757d; width: 90%; font-size: 14px; margin-top: 15px; }
        .btn-kucuk { background-color: #17a2b8; padding: 10px 15px; font-size: 14px; border:none; border-radius:4px; color:white; cursor:pointer;}
        .pasif { opacity: 0.3; pointer-events: none; }
        .durum { font-size: 20px; font-weight: bold; margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 8px;}
        .acik { color: #28a745; }
        .kapali { color: #007bff; }
        .yari { color: #fd7e14; }
        .log-kutusu { text-align: left; background: #343a40; color: #00ff00; font-family: monospace; padding: 10px; border-radius: 5px; font-size: 12px; margin-top: 20px; height: 100px; overflow: hidden; }
        input[type="number"] { padding: 8px; font-size: 14px; width: 60px; text-align:center; border: 1px solid #ccc; border-radius: 4px;}
        .kalibrasyon { margin-top: 15px; border-top: 1px dashed #ccc; padding-top: 15px; font-size: 12px; color: #555; }
        .kalibre-btn { color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; font-weight: bold; }
        @keyframes yanipsonme { 50% { opacity: 0.8; transform: scale(0.98); } }
    </style>
</head>
<body>
    <div class="kutu">
        {% if not session.get('giris_yapildi') %}
            <h2>Sisteme Giriş</h2>
            <form method="POST" action="/login">
                <input type="password" name="id_sifre" placeholder="Giriş Şifresi" required style="padding:10px; font-size:16px; width:80%; margin-bottom:10px;"><br>
                <button type="submit" class="btn btn-kapat">Bağlan</button>
            </form>
        {% else %}
            <h2 style="margin-top:0;">🏡 Akıllı Perde Paneli</h2>
            
            <div class="durum">
                Mevcut Durum: 
                {% if perde == 'acik' %}<span class="acik">TAM AÇIK</span>
                {% elif perde == 'kapali' %}<span class="kapali">TAM KAPALI</span>
                {% else %}<span class="yari">YARIMDA DURDU</span>{% endif %}
            </div>
            
            <div style="font-size: 14px; color: #555; margin-bottom: 15px;">
                <strong>Mod:</strong> {{ mod | upper }} | <strong>Sensör:</strong> <span style="font-weight:bold; color:red;">{{ isik }}</span>
            </div>

            {% if mesgul %}
                <a href="/islem/durdur" class="btn btn-durdur">ACİL DURDUR</a>
                <p style="color:red; font-weight:bold; font-size:14px;">Motor Devrede...</p>
            {% else %}
                <a href="/islem/ac" class="btn btn-ac {% if perde == 'acik' %}pasif{% endif %}">TAM AÇ</a>
                <a href="/islem/kapat" class="btn btn-kapat {% if perde == 'kapali' %}pasif{% endif %}">TAM KAPAT</a>
                
                <div style="margin-top: 15px; padding: 15px; background: #f1f3f5; border-radius: 8px;">
                    <strong style="font-size: 14px; display:block; margin-bottom:10px;">İnce Ayar (Kısmi Hareket)</strong>
                    <form method="POST" action="/kole_islem">
                        <input type="number" name="tur_miktari" placeholder="10" min="1" max="50" required onfocus="yenilemeyiDurdur()" onblur="yenilemeyiBaslat()"> Tur 
                        <button type="submit" name="yon" value="ac" class="btn-kucuk">Aç</button>
                        <button type="submit" name="yon" value="kapat" class="btn-kucuk">Kapat</button>
                    </form>
                </div>

                {% if mod == 'manuel' %}
                    <a href="/islem/otomatik" class="btn btn-oto">LDR Otomatik Modunu Başlat</a>
                {% endif %}

                <div class="kalibrasyon">
                    ⚠️ Konum Şaştıysa Sistemi Sıfırla:<br><br>
                    <a href="/kalibre/acik" class="kalibre-btn" style="background-color: #28a745;">Şu an TAM AÇIK Kabul Et</a> 
                    <a href="/kalibre/kapali" class="kalibre-btn" style="background-color: #007bff; margin-left:10px;">Şu an TAM KAPALI Kabul Et</a>
                </div>
            {% endif %}

            <div class="log-kutusu">
                {% for log in loglar %}
                    <div>{{ log }}</div>
                {% endfor %}
            </div>

            <br>
            <a href="/logout" style="color:#dc3545; font-size:12px; text-decoration:none;">Güvenli Çıkış Yap</a>
            
            <script>
                // Sayfayı 4 saniyede bir yeniler, kutuya yazarken yenilemeyi durdurur
                let yenilemeTimer = setInterval(() => location.reload(), 4000);
                function yenilemeyiDurdur() { clearInterval(yenilemeTimer); }
                function yenilemeyiBaslat() { yenilemeTimer = setInterval(() => location.reload(), 4000); }
            </script>
        {% endif %}
    </div>
</body>
</html>
"""

# ================= MOTOR ÇALIŞTIRMA İŞÇİSİ =================
def motoru_dondur_arkaplan(tur_sayisi, yon, yeni_durum, tetikleyen):
    global MOTOR_MESGUL, DURDUR_ISTEGI, PERDE_DURUMU
    MOTOR_MESGUL = True
    DURDUR_ISTEGI = False
    toplam_adim = int(tur_sayisi * ADIM_PER_TUR)
    
    if yon == "ileri": log_ekle(f"{tetikleyen} kapatıyor ({tur_sayisi} Tur).")
    else: log_ekle(f"{tetikleyen} açıyor ({tur_sayisi} Tur).")
    
    GPIO.output(ENA_PIN, GPIO.LOW) 
    time.sleep(0.2) 
    
    if yon == "ileri": GPIO.output(DIR_PIN, GPIO.HIGH)
    else: GPIO.output(DIR_PIN, GPIO.LOW)
        
    time.sleep(0.05) 
        
    for _ in range(toplam_adim):
        if DURDUR_ISTEGI:
            log_ekle("KULLANICI ACİL DURDURDU!")
            PERDE_DURUMU = "yari_acik" 
            break
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(MOTOR_HIZI)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(MOTOR_HIZI)
        
    time.sleep(0.5) 
    GPIO.output(ENA_PIN, GPIO.HIGH) 
    
    if not DURDUR_ISTEGI:
        PERDE_DURUMU = yeni_durum
        log_ekle("Hareket bitti, sistem uykuya geçti.")
        
    MOTOR_MESGUL = False
    DURDUR_ISTEGI = False

# ================= LDR SENSÖR İŞÇİSİ =================
def RCtime(RCpin):
    reading = 0
    GPIO.setup(RCpin, GPIO.OUT)
    GPIO.output(RCpin, GPIO.LOW)
    time.sleep(0.1)
    GPIO.setup(RCpin, GPIO.IN)
    while (GPIO.input(RCpin) == GPIO.LOW):
        reading += 1
        if reading > 50000: break
    return reading

def ldr_dinleyici():
    global PERDE_DURUMU, ANLIK_ISIK, SISTEM_MODU
    gunes_sayaci = 0
    karanlik_sayaci = 0
    
    while True:
        ANLIK_ISIK = RCtime(LDR_PIN)
        
        if SISTEM_MODU == "manuel" or MOTOR_MESGUL:
            time.sleep(1)
            continue
            
        if ANLIK_ISIK >= ESIK_DEGERI: 
            gunes_sayaci += 1
            if karanlik_sayaci > 0: 
                karanlik_sayaci -= 1  
        else:
            karanlik_sayaci += 1
            if gunes_sayaci > 0: 
                gunes_sayaci -= 1     

        if gunes_sayaci >= TEPKIME_SINIRI and PERDE_DURUMU in ["acik", "yari_acik"]:
            threading.Thread(target=motoru_dondur_arkaplan, args=(HEDEF_TUR, "ileri", "kapali", "LDR Sensörü")).start()
            gunes_sayaci = 0 

        elif karanlik_sayaci >= TEPKIME_SINIRI and PERDE_DURUMU in ["kapali", "yari_acik"]:
            threading.Thread(target=motoru_dondur_arkaplan, args=(HEDEF_TUR, "geri", "acik", "LDR Sensörü")).start()
            karanlik_sayaci = 0 

        time.sleep(0.5)

# ================= FLASK WEB ROUTE'LARI =================
@app.route('/')
def ana_sayfa():
    hata = request.args.get('hata')
    return render_template_string(HTML_SAYFASI, 
                                  perde=PERDE_DURUMU, 
                                  mesgul=MOTOR_MESGUL, 
                                  mod=SISTEM_MODU,
                                  isik=ANLIK_ISIK,
                                  loglar=SISTEM_LOGLARI,
                                  hata=hata)

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('id_sifre') == GIRIS_ID:
        session['giris_yapildi'] = True
        return redirect(url_for('ana_sayfa'))
    return redirect(url_for('ana_sayfa', hata=True))

@app.route('/logout')
def logout():
    session.pop('giris_yapildi', None)
    return redirect(url_for('ana_sayfa'))

@app.route('/islem/<komut>')
def islem(komut):
    global SISTEM_MODU, DURDUR_ISTEGI
    if not session.get('giris_yapildi'): return redirect(url_for('ana_sayfa'))
        
    if komut == "durdur" and MOTOR_MESGUL:
        DURDUR_ISTEGI = True
        SISTEM_MODU = "manuel"
        return redirect(url_for('ana_sayfa'))
        
    if MOTOR_MESGUL: return redirect(url_for('ana_sayfa'))

    if komut == "ac" and PERDE_DURUMU in ["kapali", "yari_acik"]:
        SISTEM_MODU = "manuel"
        threading.Thread(target=motoru_dondur_arkaplan, args=(HEDEF_TUR, "geri", "acik", "Web Paneli")).start()
        
    elif komut == "kapat" and PERDE_DURUMU in ["acik", "yari_acik"]:
        SISTEM_MODU = "manuel"
        threading.Thread(target=motoru_dondur_arkaplan, args=(HEDEF_TUR, "ileri", "kapali", "Web Paneli")).start()
        
    elif komut == "otomatik":
        SISTEM_MODU = "otomatik"
        log_ekle("Mod: Otomatik (LDR) devrede.")

    return redirect(url_for('ana_sayfa'))

@app.route('/kole_islem', methods=['POST'])
def kole_islem():
    global SISTEM_MODU
    if not session.get('giris_yapildi') or MOTOR_MESGUL: 
        return redirect(url_for('ana_sayfa'))
        
    tur_miktari = float(request.form.get('tur_miktari', 1))
    yon = request.form.get('yon')
    
    SISTEM_MODU = "manuel"
    if yon == "ac":
        threading.Thread(target=motoru_dondur_arkaplan, args=(tur_miktari, "geri", "yari_acik", "İnce Ayar")).start()
    else:
        threading.Thread(target=motoru_dondur_arkaplan, args=(tur_miktari, "ileri", "yari_acik", "İnce Ayar")).start()
        
    return redirect(url_for('ana_sayfa'))

@app.route('/kalibre/<yeni_durum>')
def kalibre(yeni_durum):
    global PERDE_DURUMU
    if not session.get('giris_yapildi') or MOTOR_MESGUL: 
        return redirect(url_for('ana_sayfa'))
        
    if yeni_durum == "acik":
        PERDE_DURUMU = "acik"
        log_ekle("KALİBRE EDİLDİ: Tam Açık.")
    elif yeni_durum == "kapali":
        PERDE_DURUMU = "kapali"
        log_ekle("KALİBRE EDİLDİ: Tam Kapalı.")
        
    return redirect(url_for('ana_sayfa'))

if __name__ == '__main__':
    threading.Thread(target=ldr_dinleyici, daemon=True).start()
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        GPIO.output(ENA_PIN, GPIO.HIGH)
        GPIO.cleanup()