@echo off
chcp 65001 >nul
title PDF Öğrenme Uygulaması
color 0B

echo.
echo ████████████████████████████████████████████████████████████████
echo ██                                                            ██
echo ██              PDF ÖĞRENME UYGULAMASI                       ██
echo ██                                                            ██
echo ██  PDF dosyalarınızı yükleyin, otomatik özetler alın ve    ██
echo ██  kişiselleştirilmiş quizlerle öğrenmenizi pekiştirin!     ██
echo ██                                                            ██
echo ████████████████████████████████████████████████████████████████
echo.

echo [1/4] Python kontrol ediliyor...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ HATA: Python yüklü değil!
    echo    Lütfen Python'u https://python.org adresinden indirin
    echo.
    pause
    exit /b 1
)
echo ✅ Python bulundu

echo.
echo [2/4] Gerekli kütüphaneler kontrol ediliyor...
python -c "import flask, PyPDF2, nltk, sklearn, pandas" 2>nul
if errorlevel 1 (
    echo ⚠️  Bazı kütüphaneler eksik, yükleniyor...
    echo.
    pip install flask PyPDF2 nltk scikit-learn pandas python-dotenv werkzeug
    if errorlevel 1 (
        echo ❌ HATA: Kütüphaneler yüklenemedi!
        echo    İnternet bağlantınızı kontrol edin
        echo.
        pause
        exit /b 1
    )
    echo ✅ Kütüphaneler yüklendi
) else (
    echo ✅ Tüm kütüphaneler mevcut
)

echo.
echo [3/4] Uygulama dosyaları kontrol ediliyor...
if not exist "app.py" (
    echo ❌ HATA: app.py dosyası bulunamadı!
    pause
    exit /b 1
)
if not exist "templates" (
    echo ❌ HATA: templates klasörü bulunamadı!
    pause
    exit /b 1
)
echo ✅ Uygulama dosyaları mevcut

echo.
echo [4/4] Uygulama başlatılıyor...
echo.
echo 🌐 Tarayıcınızda otomatik olarak açılacak: http://localhost:5000
echo.
echo 📋 Özellikler:
echo    • PDF yükleme (sürükle-bırak)
echo    • Otomatik özet oluşturma
echo    • Seviyeli quiz soruları
echo    • Dosya indirme
echo    • Kütüphane görünümü
echo.
echo ⚠️  Uygulamayı kapatmak için Ctrl+C basın
echo.

timeout /t 3 /nobreak >nul

start http://localhost:5000

python app.py

echo.
echo 👋 Uygulama kapatıldı. Teşekkürler!
echo.
pause
