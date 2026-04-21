# DiffPhys — Differensial Fizika Ta'lim Platformasi

Django-ga asoslangan veb-platforma bo'lib, fizika fanini interaktiv tarzda o'rgatish uchun mo'ljallangan.

## Asosiy imkoniyatlar

- Ma'ruzalar, taqdimotlar va amaliy materiallar
- Test tizimi
- AI modul (Hugging Face integratsiyasi, ML modellari)
- PDF generatsiya va ovozli o'qish (TTS)
- Interaktiv grafik va vizualizatsiyalar (Matplotlib, Plotly)
- Admin panel (Django Jazzmin)

## Texnologiyalar

- **Backend:** Python, Django 6.0
- **Frontend:** HTML, CSS, JavaScript
- **AI/ML:** Hugging Face, scikit-learn
- **Boshqalar:** Matplotlib, Plotly, gTTS, ReportLab, PyMuPDF

## O'rnatish

```bash
git clone <repo-url>
cd diffphys

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

`.env` fayl yarating:

```
HF_TOKEN=your_huggingface_token_here
```

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

So'ng brauzerda `http://127.0.0.1:8000` ga o'ting.

## Loyiha tuzilmasi

```
diffphys/
├── core/            # Asosiy kontent (ma'ruzalar, materiallar)
├── ai_module/       # AI va ML funksiyalari
├── users/           # Foydalanuvchi tizimi
├── testsystem/      # Test va baholash
├── materials/       # O'quv materiallari
├── videos/          # Video darslar
├── docs/            # Hujjatlar
└── templates/       # HTML shablonlar
```

## Litsenziya

MIT
