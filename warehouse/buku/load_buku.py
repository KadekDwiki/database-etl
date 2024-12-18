import mysql.connector
import pandas as pd
from datetime import datetime

def create_connection(host, user, password, database):
   conn = mysql.connector.connect(
      host=host,
      user=user,
      password=password,
      database=database
   )
   return conn

def extract_data(conn):
   query = "SELECT * FROM buku_transformed"
   df = pd.read_sql(query, conn) 
   return df

def load_data_to_warehouse(conn, df):
   cursor = conn.cursor()

   # Membuat tabel jika belum ada
   create_table_query = """
   CREATE TABLE IF NOT EXISTS dim_buku (
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

   for _, row in df.iterrows():
      # Periksa apakah data sudah ada di dim_anggota berdasarkan id dan is_current = 1
      check_query = """
      SELECT * FROM dim_buku 
      WHERE id = %s AND start_date = %s
      """
      cursor.execute(check_query, (row['id'], row['start_date']))
      existing_data = cursor.fetchone()

      if existing_data:
         print(f"Data dengan id {row['id']} sudah ada, data akan diskip.")
      else:
         # Jika data belum ada di warehouse, tambahkan data baru
         insert_query = """
         INSERT INTO dim_buku (id, judul, tahun_terbit, jumlah, isbn, pengarang_id, penerbit_id, rak_kode_rak, kategori_id, start_date, end_date, is_current)
         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
         """
         cursor.execute(insert_query, (row['id'], row['judul'], row['tahun_terbit'], row['jumlah'],
                                       row['isbn'], row['pengarang_id'], row['penerbit_id'], row['rak_kode_rak'], row['kategori_id'], row['start_date'], row['end_date'], row['is_current']))
         print(f"Data dengan id {row['id']} berhasil ditambahkan ke data warehouse.")

   # Commit perubahan
   conn.commit()
   print("Data berhasil dimuat ke dalam datawarehouse.")

# Fungsi utama untuk menjalankan ETL
def run_etl():
   source_conn = create_connection('localhost', 'root', '', 'db_perpustakaan_staging')

   # Ekstrak data dari database staging
   df = extract_data(source_conn)
   print("Data berhasil diekstraksi.")

   # Koneksi ke database warehouse
   warehouse_conn = create_connection('localhost', 'root', '', 'db_perpustakaan_warehouse')
   
   # Pindahkan data ke warehouse
   load_data_to_warehouse(warehouse_conn, df)

   # Tutup koneksi
   source_conn.close()
   warehouse_conn.close()

# Jalankan proses ETL
if __name__ == "__main__":
   run_etl()
