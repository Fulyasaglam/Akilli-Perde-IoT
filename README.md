# 🏡 Nesnelerin İnterneti (IoT) Tabanlı Akıllı Stor Perde Otomasyonu

Bu proje, sıradan bir stor perdeyi çevre bilincine sahip, güneşin durumunu analiz edebilen ve yerel ağ (LAN) üzerinden bir web paneliyle kontrol edilebilen otonom bir akıllı ev (IoT) asistanına dönüştürmek için geliştirilmiştir.

## 🚀 Proje Özellikleri

* **Otonom Karar Mekanizması:** LDR (Fotoresistor) sensörü ile ortam ışığını anlık ölçer ve güneşin durumuna göre perdeyi kendi kendine kapatır/açar.
* **Endüstriyel Gürültü Filtreleme (Anti-Flicker):** Sensörden gelen anlık parazitleri, araba farlarını veya geçici gölgeleri "Teyit ve Puanlama Algoritması" ile filtreleyerek yanlış alarmı önler.
* **Enerji Tasarrufu (Uyku Modu):** Motor hareketini tamamladığında sistem sürücü akımını keserek (ENA Pini) termal optimizasyon sağlar ve boşa güç tüketmez.
* **Asenkron Web Dashboard:** Python Flask kullanılarak geliştirilen yerel web paneli sayesinde çoklu iş parçacığı (Threading) mimarisiyle motor dönerken bile arayüz donmadan komut alır.
* **Arka Plan Servisi (Systemd):** Raspberry Pi enerji aldığı an işletim sistemi seviyesinde uyanır ve otonom döngüyü komut beklemeden başlatır.

## 🛠️ Kullanılan Teknolojiler ve Donanım
* **Ana Kontrolcü:** Raspberry Pi 
* **Yazılım & Web Sunucu:** Python, Flask, RPi.GPIO kütüphanesi
* **Tahrik Sistemi:** NEMA Step Motor & TB6600 Sürücü (1 Tur = 1600 Adım)
* **Algılayıcı:** LDR ve Kondansatör (RC Zamanlama Devresi)

## 🔌 Donanım (GPIO) Bağlantıları
* `LDR_PIN` = 3 (RC Devresi Okuma)
* `DIR_PIN` = 21 (Motor Yönü)
* `STEP_PIN` = 20 (Motor Adım Tetikleyici)
* `ENA_PIN` = 16 (Motor Uyku Modu / Akım Kesici)