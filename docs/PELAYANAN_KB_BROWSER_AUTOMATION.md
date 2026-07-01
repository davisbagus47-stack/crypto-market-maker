# Browser Automation Pelayanan KB SIGA

Modul ini menjalankan otomasi browser untuk menu:

```text
YAN KB / PELKON > Register > Pelayanan KB
```

## Status Modul

Yang sudah dibuat:

- Membaca instruksi natural user.
- Mengubah instruksi menjadi intent.
- Login ke SIGA dari browser automation.
- Membuka route `/register`.
- Klik tombol `Cari`.
- Membaca opsi dropdown SIGA untuk wilayah.
- Mencocokkan desa/RT/RW dari instruksi ke opsi SIGA.
- Klik `Cari` di popup.
- Membaca tabel hasil pencarian.
- Mengambil baris dengan `PUS = Ya`.
- Membuat file preview JSON di `data/output/`.

Yang sengaja belum diaktifkan:

- Submit final.
- Simpan final ke server SIGA.
- Perubahan massal tanpa approval.

## File Utama

- `src/browser/pelayanan_kb_automation.cjs`
- `scripts/run-pelayanan-kb-automation.cjs`
- `scripts/run-pelayanan-kb-automation.ps1`

## Persiapan `.env`

Copy file:

```powershell
copy .env.example .env
```

Isi minimal:

```env
SIGA_USERNAME=username_anda
SIGA_PASSWORD=password_anda
AGENT_DRY_RUN=true
AGENT_REQUIRE_APPROVAL=true
AGENT_HEADLESS=false
AGENT_KEEP_BROWSER_OPEN=true
```

Jangan commit `.env`.

## Cara Menjalankan

Dari folder `AI-agent`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-pelayanan-kb-automation.ps1 -CommandText "input data implant 10 orang dari desa tegalsari rt.2 rw.6"
```

Browser Chrome akan terbuka memakai profil khusus:

```text
.browser-profile/siga
```

Output preview dibuat di:

```text
data/output/
```

## Contoh Perintah

```text
input data implant 10 orang dari desa tegalsari rt.2 rw.6
```

```text
masukkan implan 5 orang dari desa sumberrejo rt 001 rw 003
```

```text
input iud 3 pus dari desa tegalrejo rt 002 rw 001
```

## Aturan Keamanan

- Jika opsi desa/RT/RW tidak ditemukan di SIGA, agent membuat warning dan tidak memaksa pilihan.
- Jika data `PUS = Ya` kurang dari jumlah yang diminta, output berstatus `partial_preview`.
- Jika `AGENT_DRY_RUN=false`, modul ini tetap belum menjalankan submit final pada versi awal.
- Submit final harus dibuat sebagai tahap terpisah setelah workflow preview benar-benar cocok dengan form SIGA.

## Troubleshooting

### Login gagal

Pastikan `.env` berisi:

```env
SIGA_USERNAME=...
SIGA_PASSWORD=...
```

### Login berhasil lalu keluar lagi

Pastikan `.env` berisi:

```env
AGENT_KEEP_BROWSER_OPEN=true
```

Script juga sekarang menunggu token SIGA tersimpan sebelum pindah ke menu `/register`. Jika output JSON berstatus `failed`, cek field `error` dan `currentUrl` di file preview `data/output/`.

Jika error menyebut `ubah kata sandi`, selesaikan ubah password manual di SIGA dulu, lalu jalankan ulang agent.

### Chrome tidak ditemukan

Set path Chrome di `.env`:

```env
CHROME_EXE=C:\Program Files\Google\Chrome\Application\chrome.exe
```

### Opsi desa tidak cocok

Gunakan nama desa seperti yang tampil di SIGA, misalnya:

```text
desa tegalsari
```

Agent akan mencocokkan ke opsi seperti:

```text
2001 - TEGALSARI
```
