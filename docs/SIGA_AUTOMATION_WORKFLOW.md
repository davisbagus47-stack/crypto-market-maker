# Workflow Otomasi Input Data SIGA

## Mode Operasi

### 1. Dry Run

Mode default. Agent hanya:

- Membaca data.
- Mapping field.
- Validasi.
- Membuat preview.
- Menyimulasikan target menu.

Tidak ada data yang dikirim ke SIGA.

### 2. Review Mode

Agent membuat file hasil validasi dan menunggu keputusan user.

Output:

- Data valid.
- Data error.
- Data warning.
- Data duplikat.
- Ringkasan mapping.

### 3. Submit Mode

Agent mengirim data ke SIGA hanya jika:

- `AGENT_DRY_RUN=false`.
- `AGENT_REQUIRE_APPROVAL=true`.
- Data sudah diberi approval.
- Tidak ada error kritis.

## Alur Detail

1. User memilih menu target.
2. User menaruh file input di `data/input/`.
3. User memilih mapping field.
4. Agent membaca data.
5. Agent melakukan normalisasi data.
6. Agent menjalankan validasi.
7. Agent membuat preview di `data/output/`.
8. User memeriksa hasil.
9. User memberi approval.
10. Agent login ke SIGA.
11. Agent membuka menu target.
12. Agent submit data per baris.
13. Agent membuat laporan hasil.

## Target Menu Prioritas

Berdasarkan menu yang sudah dipelajari, target awal yang cocok untuk otomasi input:

1. YAN KB / PELKON > Kartu Pendaftaran > Tempat Pelayanan KB
2. YAN KB / PELKON > Register > Pelayanan KB
3. YAN KB / PELKON > Register > Mutasi Alokon
4. DALLAP > Kartu Pendaftaran > Kelompok BKB
5. DALLAP > Register > Kegiatan BKB
6. Verval KRS > Keluarga Berisiko Stunting
7. ELSIMIL > Pendaftaran > Catin
8. ELSIMIL > Pendaftaran > Ibu Hamil

## Strategi per Menu

Setiap menu harus memiliki workflow sendiri di `src/workflows/`.

Contoh:

- `input_tempat_pelayanan_kb.py`
- `input_pelayanan_kb.py`
- `input_mutasi_alokon.py`
- `input_krs.py`
- `input_elsimil_catin.py`

Workflow menu harus mendefinisikan:

- Nama menu.
- URL route.
- Field wajib.
- Format data.
- Strategi submit.
- Validasi khusus.
- Risiko data.

## Aturan Submit

Agent tidak boleh submit jika:

- Ada field wajib kosong.
- Format tanggal tidak valid.
- Kode wilayah tidak cocok.
- Nomor identitas tidak valid.
- Data duplikat belum direview.
- User belum memberi approval.
- Mode masih `dry_run`.

## Output Wajib

Setiap job harus menghasilkan:

- File preview validasi.
- File hasil submit.
- File error.
- Audit log.
