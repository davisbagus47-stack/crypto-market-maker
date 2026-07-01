# Natural Language Command untuk AI Agent SIGA

Dokumen ini menjelaskan cara AI agent memahami instruksi singkat dari user dan mengubahnya menjadi rencana otomasi SIGA.

## Tujuan

User cukup memberi instruksi bahasa natural seperti:

```text
input data implant 10 orang dari desa [nama desa] rt.2 rw.6
```

Agent harus mengubah instruksi tersebut menjadi intent terstruktur:

```json
{
  "action": "input_pelayanan_kb",
  "target_menu": "yankb_pelkon.pelayanan_kb",
  "method": "IMPLAN",
  "quantity": 10,
  "participant_status": "PUS",
  "location": {
    "desa": "[NAMA DESA DARI USER]",
    "rt": "002",
    "rw": "006"
  },
  "source": "search_button",
  "submit_policy": "preview_then_approval"
}
```

## Prinsip Pemahaman

Agent harus memahami maksud, bukan hanya kata persis.

Contoh sinonim:

| Input User | Dipahami Sebagai |
| --- | --- |
| implant | IMPLAN |
| implan | IMPLAN |
| input | input_pelayanan_kb |
| masukkan | input_pelayanan_kb |
| 10 orang | quantity 10 |
| 10 data | quantity 10 |
| pus | participant_status PUS |
| rt.2 | RT 002 |
| rw.6 | RW 006 |

## Resolusi Wilayah dari SIGA

Nama desa, kelurahan, dusun, RW, dan RT tidak dipatenkan di agent.

Agent memperlakukan nilai dari instruksi user sebagai kata kunci pencarian, lalu mencocokkannya dengan opsi yang benar-benar tersedia di dropdown SIGA.

Contoh:

```text
input data implan 10 orang dari desa tegalsari rt 2 rw 6
```

Jika dropdown SIGA berisi:

```text
2001 - TEGALSARI
002 - RT 002
006 - RW 006
```

Maka agent memilih opsi tersebut. Jika tidak ada opsi yang cocok, agent harus berhenti dan meminta konfirmasi.

## Default Aman

Jika user meminta input data KB dengan metode kontrasepsi tetapi tidak menyebut NIK, agent memakai sumber:

```text
Tombol Cari > pilih data dengan PUS = Ya
```

Submit final tetap harus:

1. Membuat preview.
2. Menunggu approval.
3. Menjalankan validasi.
4. Baru submit jika disetujui.

## Informasi Minimum

Untuk otomasi penuh, instruksi minimal harus berisi:

- Aksi input.
- Metode pelayanan KB.
- Jumlah data.
- Wilayah pencarian, minimal salah satu dari desa/kecamatan/dusun/RT/RW.

Contoh valid:

```text
input data implan 10 orang dari desa tegalsari rt 1 rw 1
```

Contoh kurang lengkap:

```text
input data implan
```

Agent harus meminta detail jumlah dan wilayah.

## Ambiguitas

Jika nama wilayah bisa berarti kecamatan atau desa, agent boleh tetap membuat intent tetapi memberi warning.

Contoh:

```text
input data implant 10 orang dari ambulu rt 2 rw 6
```

Hasil:

- `kecamatan`: belum pasti
- `desa`: AMBULU
- `needs_confirmation`: true
- alasan: nama wilayah tanpa kata desa/kecamatan berpotensi ambigu

## Rencana Eksekusi Setelah Intent Terbentuk

1. Login SIGA.
2. Buka menu `YAN KB / PELKON > Register > Pelayanan KB`.
3. Klik tombol `Cari`.
4. Baca opsi wilayah yang tersedia di SIGA.
5. Cocokkan desa/RT/RW dari instruksi dengan opsi SIGA.
6. Jika opsi tidak cocok atau ambigu, berhenti dan minta konfirmasi.
7. Klik `Cari` pada popup.
8. Baca tabel hasil.
9. Pilih hanya baris `PUS = Ya`.
10. Jika belum cukup, lanjut pagination.
11. Ambil sesuai jumlah yang diminta.
12. Isi form pelayanan KB dengan metode yang diminta.
13. Simpan sementara.
14. Buat preview hasil.
15. Tunggu approval sebelum submit final.

## Contoh Perintah

```text
input data implant 10 orang dari desa tegalsari rt.2 rw.6
```

```text
masukkan implan 5 pus dari desa tegalsari dusun bedengan rw 01 rt 001
```

```text
input suntik 20 orang pus dari kecamatan ambulu desa tegalsari
```

```text
buat pelayanan kb iud 3 orang dari rt 001 rw 002, preview dulu
```
