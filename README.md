# Aku Sehat AI — Consistent Nutrition Fields

Versi ini menyamakan variabel input manual dengan variabel nutrisi yang ditampilkan pada analisis gambar AI:

- Kalori (kcal)
- Protein (g)
- Lemak (g)
- Karbohidrat (g)

Variabel serat, gula, dan natrium dihapus dari input manual dan hasil estimasi komponen AI karena tidak menjadi bagian dari empat variabel inti dataset Nutrition Indonesia yang digunakan.

## Menjalankan

```powershell
python -m streamlit run app.py
```

Syntax `app.py` telah diperiksa menggunakan `py_compile`.
