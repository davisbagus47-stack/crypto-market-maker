# AI Agent Input Data Otomatis SIGA

Project ini adalah struktur awal AI agent untuk membantu input data otomatis ke web SIGA:

`https://newsiga-siga.bkkbn.go.id`

Fokus awal agent:

- Membaca data sumber dari CSV atau Excel.
- Mencocokkan kolom data sumber ke field target SIGA.
- Memvalidasi data sebelum input.
- Menampilkan hasil review sebelum submit.
- Menginput data ke menu SIGA yang dipilih setelah approval.
- Membuat log dan laporan hasil proses.

## Prinsip Keamanan

- Password dan token tidak disimpan di repository.
- Kredensial diletakkan di `.env` lokal.
- Mode default harus `dry_run`.
- Submit data ke SIGA hanya boleh dilakukan setelah review dan approval.
- Semua aktivitas wajib dicatat di `logs/`.

## Struktur Folder

```text
AI-agent/
├── config/
│   ├── agent.config.example.json
│   ├── field_mapping.example.json
│   └── siga_menu_targets.json
├── data/
│   ├── input/
│   ├── output/
│   └── templates/
├── docs/
│   ├── AI_AGENT_ARCHITECTURE.md
│   ├── SIGA_AUTOMATION_WORKFLOW.md
│   └── SECURITY_AND_APPROVAL.md
├── logs/
├── prompts/
│   └── siga_data_entry_agent.md
├── src/
│   ├── agent/
│   ├── integrations/
│   ├── siga/
│   ├── validation/
│   └── workflows/
└── tests/
```

## Alur Kerja Agent

1. Operator menaruh file input di `data/input/`.
2. Agent membaca konfigurasi menu dan mapping field.
3. Agent memvalidasi data.
4. Agent membuat preview hasil validasi.
5. Operator melakukan review.
6. Jika disetujui, agent login ke SIGA.
7. Agent membuka menu target atau endpoint target.
8. Agent menginput data per baris.
9. Agent menyimpan hasil proses ke `data/output/` dan `logs/`.

## Perintah Bahasa Natural

Agent disiapkan untuk memahami instruksi singkat seperti:

```text
input data implant 10 orang dari desa [nama desa] rt.2 rw.6
```

Instruksi tersebut diparse menjadi intent terstruktur berisi target menu, metode KB, jumlah data, status peserta, wilayah, dan kebijakan submit. Nama desa/RT/RW kemudian dicocokkan dengan opsi yang tersedia di SIGA saat eksekusi.

Dokumen detail:

- `docs/NATURAL_LANGUAGE_COMMANDS.md`

Contoh menjalankan parser:

```bash
python parse_command.py "input data implant 10 orang dari desa tegalsari rt.2 rw.6"
```

## Menu SIGA yang Sudah Dipetakan

Ringkasan menu akun operator tersedia di:

- `SIGA_Menu_Map.md`
- `config/siga_menu_targets.json`

## Tahap Pengembangan Berikutnya

1. Tentukan menu target pertama yang ingin diotomatisasi.
2. Ambil contoh file input.
3. Buat mapping field sesuai form SIGA.
4. Implementasikan workflow khusus menu tersebut di `src/workflows/`.
5. Jalankan validasi dan dry-run.
6. Aktifkan submit setelah hasil dry-run benar.

## Cara Menjalankan

Lihat panduan:

- `docs/RUNNING.md`
- `docs/PELAYANAN_KB_BROWSER_AUTOMATION.md`
