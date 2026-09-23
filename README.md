# Aku Sehat AI — Automatic Correction Re-analysis V5

## Alur analisis makanan
1. Gemini menganalisis gambar dan menghasilkan estimasi awal.
2. Pengguna mengoreksi nama makanan pada input.
3. Tekan **Enter** setelah mengubah nama untuk menjalankan analisis ulang AI secara otomatis; tidak ada tombol analisis ulang terpisah.
4. AI menganalisis ulang gambar yang sama dengan nama dan berat koreksi.
5. Dataset Nutrition Indonesia digunakan hanya sebagai referensi jika kecocokan nama tervalidasi.
6. Jika tidak ada kecocokan dataset yang cukup kuat, hasil analisis ulang AI digunakan sebagai sumber nutrisi.
7. Pengguna tetap menekan tombol konfirmasi untuk menyimpan hasil final.

## Konfigurasi Streamlit Secrets
```toml
SUPABASE_URL = "..."
SUPABASE_KEY = "..."
GEMINI_API_KEY = "..."
GEMINI_MODEL = "gemini-3.6-flash"
```

## Menjalankan lokal
```bash
pip install -r requirements.txt
streamlit run app.py
```

Catatan: API call Gemini tetap membutuhkan API key aktif dan kuota yang tersedia.
