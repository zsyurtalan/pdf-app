@echo off
title PDF Ogrenme Uygulamasi
color 0A

echo.
echo ========================================
echo    PDF OGRENME UYGULAMASI BASLATILIYOR
echo ========================================
echo.

echo Gerekli kutuphaneler kontrol ediliyor...
python -c "import flask, PyPDF2, nltk, sklearn, pandas" 2>nul
if errorlevel 1 (
    echo Kutuphaneler yukleniyor...
    pip install flask PyPDF2 nltk scikit-learn pandas python-dotenv werkzeug
    if errorlevel 1 (
        echo HATA: Kutuphaneler yuklenemedi!
        pause
        exit /b 1
    )
)

echo.
echo Uygulama baslatiliyor...
echo Tarayicinizda http://localhost:5000 adresini acin
echo.

timeout /t 2 /nobreak >nul
start http://localhost:5000

echo Uygulamayi kapatmak icin Ctrl+C basin
echo.

python app.py

echo.
echo Uygulama kapatildi.
pause
