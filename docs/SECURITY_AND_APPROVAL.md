# Keamanan dan Approval

## Data Sensitif

SIGA dapat berisi data pribadi dan data program. Agent harus memperlakukan semua input dan output sebagai data sensitif.

Contoh data sensitif:

- Nama penduduk.
- NIK.
- Alamat.
- Nomor telepon.
- Data kesehatan.
- Data keluarga.
- Data pelayanan KB.
- Data kehamilan dan baduta.

## Larangan

Agent tidak boleh:

- Menyimpan password di file project.
- Menulis token login ke log.
- Submit data tanpa approval.
- Mengabaikan error validasi kritis.
- Melakukan perubahan massal tanpa laporan preview.
- Menghapus data di SIGA kecuali ada instruksi eksplisit dan approval terpisah.

## Approval Gate

Approval diperlukan sebelum:

- Submit data baru.
- Update data lama.
- Retry data gagal dalam jumlah besar.
- Mengirim data yang mengandung warning.
- Menggunakan browser automation untuk submit form.

## Isi Audit Log

Audit log boleh berisi:

- Job id.
- Waktu proses.
- Username operator.
- Nama menu target.
- Nama file input.
- Jumlah data diproses.
- Jumlah berhasil dan gagal.
- Pesan error teknis.

Audit log tidak boleh berisi:

- Password.
- Access token.
- Refresh token.
- Cookie sesi.
- Data pribadi lengkap jika tidak diperlukan.

## Rekomendasi Operasional

- Mulai dari batch kecil 3 sampai 5 baris.
- Jalankan dry-run sebelum submit.
- Cocokkan hasil input di SIGA secara manual untuk batch pertama.
- Naikkan jumlah batch setelah workflow stabil.
- Simpan backup file input.
