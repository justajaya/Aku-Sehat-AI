# Aku Sehat AI Premium v6

Versi ini memakai background CSS tanpa pseudo-element atau z-index negatif dan menampilkan pesan kesalahan Supabase di halaman.

## Jalankan di Windows
1. Ekstrak ZIP. Buka folder `aku_sehat_ai_premium_v6` langsung di VS Code (jangan folder induk).
2. Instal Python 3.12 dari python.org jika belum ada.
3. Salin `.env.example` menjadi `.env` dan isi dengan **kunci baru**. Jangan unggah `.env` ke GitHub.
4. Klik `run.bat` atau jalankan `py -3.12 -m venv .venv`, `.venv\Scripts\python.exe -m pip install -r requirements.txt`, lalu `.venv\Scripts\python.exe -m streamlit run app.py`.
5. Buka http://localhost:8501. Jika port lama masih digunakan, hentikan proses Streamlit lama dengan Ctrl+C.

## Penyimpanan
Jalankan `supabase_schema.sql` di SQL Editor proyek Supabase jika tabel belum tersedia. Gunakan **anon/publishable key**, bukan service-role key.

## Analisis makanan
AI membaca gambar lebih dahulu. Hanya exact match nama hidangan lengkap yang boleh memakai data nutrisi dataset; jika tidak cocok gunakan estimasi AI dan tampilkan sumbernya. Koreksi membutuhkan analisis ulang gambar. Angka dari gambar adalah estimasi, bukan pengukuran laboratorium.

## Diagnostik
Jika masih putih: buka `http://localhost:8501/_stcore/health`, cek terminal dan DevTools Console. Jalankan `python -m streamlit run app.py` dari folder proyek.


### Final UI cleanup
Tiga wrapper dekoratif macro-panel/macro-legend yang menyebabkan bubble kosong telah dihapus. Perhitungan makronutrien, chart, Gemini, dataset exact-match, dan alur aplikasi tidak diubah.


### Perkembangan Kalori
Menambahkan visualisasi tren kalori 7 hari dari riwayat makanan, rata-rata, kalori hari ini, target harian, serta garis konsumsi vs target.


### Perbaikan sumber data grafik kalori
Grafik perkembangan kalori kini membaca langsung dari tabel `meals` Supabase untuk 7 hari sampai tanggal yang dipilih, sehingga tidak lagi bergantung pada session state yang kosong.


### Perkembangan Kalori
Grafik perkembangan kalori hanya ditampilkan pada tab Dashboard.


### AI Personal Nutrition Coach
Menambahkan insight AI opsional di Dashboard. Gemini menganalisis target, makanan tercatat, makronutrien, dan tren 7 hari untuk ringkasan, insight pola, dan saran makan berikutnya.

### Final integrated revision
- AI Personal Nutrition Coach menggunakan Gemini untuk menganalisis target, makanan tercatat, makronutrien, dan tren 7 hari.
- Grafik perkembangan kalori hanya dirender pada Dashboard.
- Grafik mengambil data langsung dari tabel riwayat makanan/Supabase.


## Gemini API — current configuration
The project uses `gemini-3.8-flash` by default. Google currently limits access to Gemini 2.5 models for many new users/projects, so old `gemini-2.5-flash` settings are normalized to a current Flash model.

Before running the application, test the API with:

```powershell
python test_gemini.py
```

A successful test prints `GEMINI_OK`. The application never stores the API key in source code.

## Recommendation AI
The recommendation workflow is intentionally split into two layers:
1. Python filters and scores candidates using the existing `data/nutrition.csv` dataset and calculates numeric portions.
2. Gemini receives only those validated candidates and is used to select/combine/explain the recommendation.

Therefore Gemini is not allowed to invent calorie or protein values for the recommendation.
