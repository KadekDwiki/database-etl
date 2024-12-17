import mysql.connector
import pandas as pd
from datetime import datetime

# 1. Fungsi untuk menghubungkan ke database MySQL
def create_connection(host, user, password, database):
   conn = mysql.connector.connect(
      host=host,
      user=user,
      password=password,
      database=database
   )
   return conn

# 2. Fungsi untuk mengekstraksi data (Extract)
def extract_data(conn):
   query = "SELECT * FROM buku" 
   df = pd.read_sql(query, conn) 
   return df

# 3. Fungsi untuk mentransformasikan data (Transform)
def transform_data(df):
   rata_rata_jumlah = df['jumlah'].mean()
   
   df['judul'] = df['judul'].replace(r'^\s*$', None, regex=True)
   df['tahun_terbit'] = df['tahun_terbit'].replace(r'^\s*$', None, regex=True)
   df['jumlah'] = df['jumlah'].replace(r'^\s*$', None, regex=True)
   df['isbn'] = df['isbn'].replace(r'^\s*$', None, regex=True)
   
   df.fillna({
            'judul': 'Tidak diketahui',
            'tahun_terbit': datetime.now().year,
            'jumlah': rata_rata_jumlah,
            'isbn': '-'
            },
            inplace=True)
   
   return df

# 4. Fungsi untuk memuat data ke staging area (Load)
def load_data_to_staging(conn, df):
   cursor = conn.cursor()

   create_table_query = """
   CREATE TABLE IF NOT EXISTS buku_transformed (
      id INT,
      judul VARCHAR(100),
      tahun_terbit INT,
      jumlah INT,
      isbn VARCHAR(45),
      pengarang_id INT,
      penerbit_id INT,
      rak_kode_rak VARCHAR(10),
      kategori_id INT,
      start_date DATETIME,
      end_date DATETIME,
      is_current BOOLEAN,
      PRIMARY KEY (id, start_date)
   )
   """
   cursor.execute(create_table_query)
   
   # Memasukkan data yang sudah ditransformasikan ke dalam tabel tujuan di staging area
   for _, row in df.iterrows():
      # Periksa apakah data sudah ada dan perlu diperbarui
      check_query = """
      SELECT * FROM buku_transformed 
      WHERE id = %s AND is_current = 1
      """
      cursor.execute(check_query, (row['id'],))
      existing_data = cursor.fetchone()
      
      # Jika data lama ada dan berbeda, nonaktifkan data lama dan tambahkan data baru
      if existing_data:
         current_values = existing_data[1:9]
         new_values = (row['judul'], row['tahun_terbit'], row['jumlah'], row['isbn'], row['pengarang_id'], row['penerbit_id'], row['rak_kode_rak'], row['kategori_id'])

         if current_values != new_values:
               # Nonaktifkan data lama
               update_old_query = """
               UPDATE buku_transformed
               SET end_date = %s, is_current = 0
               WHERE id = %s AND is_current = 1
               """
               cursor.execute(update_old_query, (datetime.now(), row['id']))

               # Tambahkan data baru
               insert_new_query = """
               INSERT INTO buku_transformed (id, judul, tahun_terbit, jumlah, isbn, pengarang_id, penerbit_id, rak_kode_rak, kategori_id, start_date, end_date, is_current)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, 1)
               """
               cursor.execute(insert_new_query, (row['id'], row['judul'], row['tahun_terbit'], row['jumlah'],
                                                row['isbn'], row['pengarang_id'], row['penerbit_id'], row['rak_kode_rak'], row['kategori_id'], datetime.now()))
      else:
         # Jika data belum ada, tambahkan sebagai data baru
         insert_query = """
         INSERT INTO buku_transformed (id, judul, tahun_terbit, jumlah, isbn, pengarang_id, penerbit_id, rak_kode_rak, kategori_id, start_date, end_date, is_current)
         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, 1)
         """
         cursor.execute(insert_query, (row['id'], row['judul'], row['tahun_terbit'], row['jumlah'],
                                       row['isbn'], row['pengarang_id'], row['penerbit_id'], row['rak_kode_rak'], row['kategori_id'], datetime.now()))

   conn.commit()
   print("Data berhasil dimuat ke dalam database dengan SCD type 2.")

# Fungsi utama untuk menjalankan ETL
def run_etl():
   # 1. Buat koneksi ke database sumber
   source_conn = create_connection('localhost', 'root', '', 'db_perpustakaan')

   # 2. Ekstraksi data
   df = extract_data(source_conn)
   print("Data berhasil diekstraksi.")
   
   # 3. Transformasi data to staging area
   transformed_df = transform_data(df)
   print("Data berhasil ditransformasikan.")
   # return print(df)

   # 4. Buat koneksi ke database tujuan
   staging_conn = create_connection('localhost', 'root', '', 'db_perpustakaan_staging')
   
   # 5. Memuat data ke database tujuan
   load_data_to_staging(staging_conn, transformed_df)

   # 6. Tutup koneksi
   source_conn.close()
   staging_conn.close()

# Jalankan proses ETL
if __name__ == "__main__":
   run_etl()