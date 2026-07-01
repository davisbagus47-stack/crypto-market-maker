# PRD: AI Agent untuk Input Data Otomatis

## 1. Ringkasan Produk

AI Agent untuk Input Data Otomatis adalah sistem yang membantu pengguna membaca, memvalidasi, dan menginput data dari berbagai sumber ke sistem tujuan secara otomatis.

Produk ini ditujukan untuk mengurangi pekerjaan input data manual, mempercepat proses operasional, mengurangi risiko kesalahan, serta menyediakan proses yang dapat ditinjau dan diaudit.

## 2. Latar Belakang Masalah

Banyak proses bisnis masih mengandalkan input data manual, seperti:

- Menyalin data dari Excel ke aplikasi internal.
- Menginput data invoice dari PDF ke sistem akuntansi.
- Memasukkan data pelanggan ke CRM.
- Memindahkan data dari email atau formulir ke spreadsheet.
- Menginput data absensi, order, survei, atau laporan harian.

Masalah utama yang muncul:

- Proses memakan waktu.
- Rawan kesalahan manusia.
- Sulit diskalakan saat volume data meningkat.
- Tidak ada validasi otomatis sebelum data masuk.
- Aktivitas input sulit diaudit jika tidak ada log yang rapi.

## 3. Tujuan Produk

Tujuan utama produk:

- Mengotomatisasi proses ekstraksi dan input data.
- Memvalidasi data sebelum dikirim ke sistem tujuan.
- Memberikan halaman review sebelum submit.
- Menyediakan audit trail untuk setiap proses.
- Menghasilkan laporan berhasil, gagal, duplikat, dan data yang perlu dicek.

## 4. Target Pengguna

- Admin operasional.
- Tim finance dan accounting.
- Tim sales support.
- Tim HR.
- Tim customer service.
- Tim data entry.
- Supervisor operasional.
- Pemilik bisnis kecil dan menengah.

## 5. Ruang Lingkup Produk

### In Scope MVP

- Upload file Excel dan CSV.
- Preview data hasil upload.
- Field mapping dari data sumber ke field tujuan.
- Validasi data wajib, format email, nomor telepon, tanggal, dan duplikasi sederhana.
- Review data sebelum submit.
- Submit data ke Google Sheet, database, atau API sederhana.
- Log proses input.
- Export laporan error.

### Out of Scope MVP

- OCR PDF dan gambar.
- Browser automation untuk sistem tanpa API.
- Integrasi kompleks dengan ERP atau CRM.
- Multi-step approval.
- AI correction lanjutan.
- Scheduled automation.
- Multi-tenant enterprise.

## 6. Use Case Utama

### UC-001: Upload Data dari Excel atau CSV

Pengguna mengunggah file Excel atau CSV berisi data yang ingin diinput ke sistem tujuan. Sistem membaca file dan menampilkan preview data.

### UC-002: Mapping Field

Pengguna mencocokkan kolom sumber dengan field tujuan. Mapping dapat disimpan sebagai template untuk proses berikutnya.

Contoh mapping:

| Data Sumber | Field Tujuan |
| --- | --- |
| Nama Customer | customer_name |
| No HP | phone_number |
| Email | email |
| Total Tagihan | invoice_amount |
| Tanggal Transaksi | transaction_date |

### UC-003: Validasi Data

Sistem memeriksa data sebelum submit. Baris data diberi status valid, error, duplikat, atau perlu dicek.

### UC-004: Review Sebelum Submit

Pengguna dapat meninjau data, memperbaiki error, dan memilih baris mana yang akan dikirim ke sistem tujuan.

### UC-005: Auto Input ke Sistem Tujuan

AI Agent mengirim data ke sistem tujuan melalui API, database, atau Google Sheet.

### UC-006: Laporan Hasil Input

Setelah proses selesai, sistem menampilkan ringkasan hasil input dan menyediakan file laporan.

## 7. Alur Pengguna

1. Pengguna login ke aplikasi.
2. Pengguna memilih proses input data.
3. Pengguna mengunggah file Excel atau CSV.
4. Sistem membaca isi file dan menampilkan preview.
5. Pengguna melakukan field mapping.
6. Sistem menjalankan validasi.
7. Pengguna meninjau data valid, error, dan duplikat.
8. Pengguna memperbaiki data jika diperlukan.
9. Pengguna menekan tombol submit.
10. AI Agent menginput data ke sistem tujuan.
11. Sistem menampilkan laporan hasil proses.

## 8. Fitur Utama

### 8.1 Upload dan Import Data

Sistem menerima file:

- CSV.
- XLSX.
- XLS.

Ketentuan:

- Maksimal ukuran file MVP: 10 MB.
- Maksimal jumlah baris MVP: 10.000 baris.
- Header kolom wajib tersedia di baris pertama.

### 8.2 Data Preview

Sistem menampilkan preview data sebelum diproses.

Informasi yang ditampilkan:

- Nama kolom.
- Contoh nilai.
- Jumlah baris.
- Jumlah kolom.
- Deteksi nilai kosong.

### 8.3 Field Mapping

Pengguna dapat menghubungkan kolom sumber ke field tujuan.

Kemampuan field mapping:

- Manual mapping.
- Auto-suggestion mapping berdasarkan nama kolom.
- Simpan mapping sebagai template.
- Gunakan ulang template mapping.

### 8.4 Validasi Data

Validasi minimal:

- Field wajib tidak boleh kosong.
- Format email valid.
- Nomor telepon valid.
- Format tanggal valid.
- Nilai angka valid.
- Deteksi duplikasi berdasarkan field kunci.
- Panjang karakter sesuai batas field tujuan.

### 8.5 Confidence dan Status Data

Setiap baris data memiliki status:

- Valid: data siap dikirim.
- Warning: data dapat dikirim tetapi sebaiknya dicek.
- Error: data tidak dapat dikirim sebelum diperbaiki.
- Duplicate: data terindikasi sudah ada.

### 8.6 Review dan Edit Data

Pengguna dapat:

- Mengedit nilai data langsung di tabel review.
- Memfilter baris berdasarkan status.
- Memilih baris yang akan diproses.
- Mengabaikan baris tertentu.
- Mengunduh daftar error.

### 8.7 Submit Otomatis

Sistem mengirim data ke tujuan melalui:

- REST API.
- Database.
- Google Sheet.
- Sistem internal yang sudah memiliki endpoint integrasi.

### 8.8 Retry dan Error Handling

Jika proses submit gagal:

- Sistem menyimpan status gagal.
- Sistem menampilkan alasan gagal.
- Pengguna dapat menjalankan retry.
- Sistem mencegah submit ganda untuk data yang sudah berhasil.

### 8.9 Log dan Audit Trail

Sistem mencatat:

- User yang menjalankan proses.
- Waktu upload.
- Nama file.
- Mapping yang digunakan.
- Jumlah data berhasil dan gagal.
- Error dari sistem tujuan.
- Perubahan data sebelum submit.

### 8.10 Laporan Hasil

Sistem menampilkan:

- Total data diproses.
- Jumlah berhasil.
- Jumlah gagal.
- Jumlah duplikat.
- Jumlah warning.
- File laporan hasil proses.

## 9. User Stories

- Sebagai admin, saya ingin mengunggah file Excel agar data dapat dibaca otomatis oleh sistem.
- Sebagai operator, saya ingin memetakan kolom sumber ke field tujuan agar data masuk ke tempat yang benar.
- Sebagai finance, saya ingin sistem memvalidasi data nominal dan tanggal agar tidak terjadi salah input.
- Sebagai supervisor, saya ingin meninjau data sebelum submit agar data penting tidak langsung masuk tanpa kontrol.
- Sebagai manager, saya ingin melihat log proses agar aktivitas input data dapat diaudit.
- Sebagai operator, saya ingin mengunduh daftar error agar bisa memperbaiki data dengan cepat.

## 10. Functional Requirements

| ID | Requirement | Prioritas |
| --- | --- | --- |
| FR-001 | Sistem dapat menerima upload file CSV, XLS, dan XLSX | High |
| FR-002 | Sistem dapat membaca header dan isi file | High |
| FR-003 | Sistem dapat menampilkan preview data | High |
| FR-004 | Sistem dapat melakukan field mapping | High |
| FR-005 | Sistem dapat menyimpan template mapping | Medium |
| FR-006 | Sistem dapat melakukan validasi data dasar | High |
| FR-007 | Sistem dapat menandai status valid, warning, error, dan duplikat | High |
| FR-008 | Sistem menyediakan halaman review sebelum submit | High |
| FR-009 | Pengguna dapat mengedit data di halaman review | High |
| FR-010 | Sistem dapat submit data ke sistem tujuan | High |
| FR-011 | Sistem menyimpan log proses | High |
| FR-012 | Sistem dapat menampilkan laporan hasil proses | High |
| FR-013 | Sistem dapat melakukan retry untuk data gagal | Medium |
| FR-014 | Sistem dapat export laporan error | Medium |

## 11. Non-Functional Requirements

- Sistem harus dapat memproses minimal 10.000 baris data per upload untuk MVP.
- Preview data maksimal tampil dalam 5 detik untuk file kecil di bawah 1.000 baris.
- Semua aktivitas penting harus tercatat di audit log.
- Data sensitif harus dienkripsi saat disimpan.
- Sistem harus menggunakan role-based access control.
- Sistem harus memiliki mekanisme retry untuk kegagalan submit.
- Sistem harus mencegah duplikasi data pada proses submit ulang.
- Sistem harus menyediakan pesan error yang jelas dan dapat ditindaklanjuti.

## 12. Role dan Permission

| Role | Permission |
| --- | --- |
| Admin | Kelola user, integrasi, template, dan audit log |
| Operator | Upload, mapping, review, edit, dan submit data |
| Reviewer | Review, approve, atau reject data |
| Viewer | Melihat laporan dan log |

## 13. Integrasi

Integrasi MVP:

- Google Sheets.
- Database SQL.
- REST API internal.

Integrasi lanjutan:

- CRM.
- ERP.
- Accounting software.
- Email inbox.
- Browser automation untuk sistem tanpa API.

## 14. Data Model Awal

### Import Job

| Field | Deskripsi |
| --- | --- |
| id | ID proses import |
| user_id | User yang membuat proses |
| source_file_name | Nama file sumber |
| status | Status proses |
| total_rows | Jumlah total baris |
| success_rows | Jumlah berhasil |
| failed_rows | Jumlah gagal |
| duplicate_rows | Jumlah duplikat |
| created_at | Waktu proses dibuat |
| completed_at | Waktu proses selesai |

### Import Row

| Field | Deskripsi |
| --- | --- |
| id | ID baris data |
| import_job_id | Relasi ke import job |
| row_number | Nomor baris dari file sumber |
| raw_data | Data asli |
| mapped_data | Data setelah mapping |
| validation_status | Status validasi |
| error_message | Pesan error jika ada |
| submit_status | Status submit |

### Mapping Template

| Field | Deskripsi |
| --- | --- |
| id | ID template |
| name | Nama template |
| source_type | Jenis sumber data |
| destination_type | Jenis tujuan |
| mapping_config | Konfigurasi mapping |
| created_by | Pembuat template |

## 15. Acceptance Criteria MVP

MVP dianggap selesai jika:

- Pengguna dapat mengunggah file CSV atau Excel.
- Sistem dapat membaca dan menampilkan preview data.
- Pengguna dapat melakukan mapping field.
- Sistem dapat menjalankan validasi data wajib.
- Sistem dapat menampilkan status valid, error, warning, dan duplikat.
- Pengguna dapat memperbaiki data sebelum submit.
- Sistem dapat mengirim data valid ke tujuan.
- Sistem dapat menampilkan jumlah berhasil dan gagal.
- Sistem menyimpan audit log proses.
- Pengguna dapat mengunduh laporan error.

## 16. Success Metrics

- Waktu input data manual berkurang minimal 60%.
- Error input data turun minimal 50%.
- Minimal 90% data valid dapat diproses tanpa intervensi tambahan.
- Minimal 80% pengguna target menggunakan fitur ini setiap minggu.
- Waktu rata-rata proses batch lebih cepat daripada proses manual.
- Jumlah data gagal menurun dari waktu ke waktu.

## 17. Risiko dan Mitigasi

| Risiko | Dampak | Mitigasi |
| --- | --- | --- |
| Format file tidak konsisten | Data gagal dibaca | Sediakan template upload dan validasi struktur |
| Mapping field salah | Data masuk ke field yang keliru | Tambahkan review dan template mapping |
| Data duplikat terkirim | Data tujuan tidak bersih | Gunakan duplicate detection dan idempotency key |
| Integrasi API gagal | Proses input berhenti | Tambahkan retry, checkpoint, dan error report |
| Data sensitif bocor | Risiko keamanan tinggi | Enkripsi, RBAC, dan audit log |
| Pengguna melewati review | Data salah terkirim | Wajibkan review untuk data high risk |

## 18. Roadmap

### Phase 1: MVP

- Upload CSV dan Excel.
- Preview data.
- Field mapping.
- Validasi dasar.
- Review data.
- Submit ke Google Sheet, database, atau API.
- Log dan laporan error.

### Phase 2: AI Extraction

- OCR PDF dan gambar.
- Confidence score.
- Auto-suggestion koreksi data.
- Template dokumen.

### Phase 3: Advanced Automation

- Browser automation.
- Integrasi CRM dan ERP.
- Multi-step approval.
- Scheduled automation.

### Phase 4: Enterprise

- Multi-tenant support.
- Advanced audit compliance.
- Public API.
- Dashboard analytics.
- Custom role dan permission.

## 19. Rekomendasi Arsitektur Awal

Komponen sistem:

- Frontend untuk upload, mapping, review, dan laporan.
- Backend API untuk proses import, validasi, dan submit.
- Worker queue untuk proses batch.
- Database untuk import job, row status, template, dan audit log.
- Integration layer untuk Google Sheet, API, dan database tujuan.
- AI layer untuk auto-mapping dan ekstraksi lanjutan.

Alur teknis:

1. File diunggah ke backend.
2. Backend menyimpan file dan membuat import job.
3. Worker membaca file dan membuat preview data.
4. Pengguna membuat atau memilih mapping.
5. Worker menjalankan validasi.
6. Pengguna review dan submit.
7. Worker mengirim data ke sistem tujuan.
8. Sistem memperbarui status dan membuat laporan.

## 20. Catatan Implementasi

Prioritas implementasi sebaiknya dimulai dari CSV dan Excel karena struktur datanya lebih jelas, validasi lebih mudah, dan dampaknya cepat terasa bagi pengguna. Setelah alur upload, mapping, validasi, review, dan submit stabil, fitur AI lanjutan seperti OCR dan browser automation dapat ditambahkan secara bertahap.
