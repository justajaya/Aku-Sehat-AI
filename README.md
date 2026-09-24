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
