# Cara Menjalankan AI Agent SIGA

## Status Saat Ini

Yang sudah bisa dijalankan:

- Parse instruksi bahasa natural.
- Membaca intent seperti metode KB, jumlah, desa, RT, dan RW.
- Dry-run file CSV contoh.
- Mapping field.
- Validasi data.
- Membuat preview di `data/output/`.
- Membuat audit log di `logs/`.

Yang belum diaktifkan:

- Submit final ke SIGA.
- Simpan final ke server SIGA.

Alasan submit belum aktif: agar agent tidak mengubah data produksi sebelum workflow form SIGA benar-benar diverifikasi.

## 1. Parse Instruksi Natural

Dari PowerShell di folder `AI-agent`, jalankan:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\parse-intent.ps1 -CommandText "input data implant 10 orang dari desa tegalsari rt.2 rw.6"
```

Output akan berisi:

- Target menu.
- Metode KB.
- Jumlah data.
- Status peserta `PUS`.
- Lokasi desa/RT/RW.
- Rencana eksekusi.

## 2. Dry-run Data Contoh

Dari PowerShell di folder `AI-agent`, jalankan:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\dry-run-sample.ps1
```

Output akan menampilkan job id dan file preview.

Preview dibuat di:

```text
data/output/
```

Audit log dibuat di:

```text
logs/
```

## 3. Jalankan Manual dengan Python

Jika ingin menjalankan langsung:

```powershell
C:\Users\davis\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe parse_command.py "input data implant 10 orang dari desa tegalsari rt.2 rw.6"
```

Dry-run manual:

```powershell
C:\Users\davis\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe run_agent.py --input data\templates\sample_input_tempat_pelayanan_kb.csv
```

## 4. Jalankan Browser Automation Pelayanan KB

Siapkan `.env`:

```powershell
copy .env.example .env
```

Isi `SIGA_USERNAME` dan `SIGA_PASSWORD` di `.env`.

Lalu jalankan:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-pelayanan-kb-automation.ps1 -CommandText "input data implant 10 orang dari desa tegalsari rt.2 rw.6"
```

Modul ini membuka Chrome, login, membuka menu Pelayanan KB, klik Cari, mencari data `PUS = Ya`, lalu membuat preview JSON di `data/output/`.

Panduan detail:

- `docs/PELAYANAN_KB_BROWSER_AUTOMATION.md`

## Tahap Berikutnya

Agar submit final bisa aktif, workflow berikut perlu diverifikasi:

1. Pilih baris PUS dari popup.
2. Tambahkan peserta ke form.
3. Isi field wajib pelayanan KB.
4. Klik Simpan Sementara.
5. Cocokkan hasil preview dengan data di halaman.
6. Aktifkan submit final setelah approval.
