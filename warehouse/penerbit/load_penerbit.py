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
   query = "SELECT * FROM penerbit_transformed"  # Gantilah nama tabel dengan tabel yang sesuai
   df = pd.read_sql(query, conn) 
   return df

def load_data_to_warehouse(conn, df):
   cursor = conn.cursor()

   # Membuat tabel jika belum ada
   create_table_query = """
   CREATE TABLE IF NOT EXISTS dim_penerbit (
      id INT PRIMARY KEY,
      nama VARCHAR(255),
      telp VARCHAR(12),
      alamat TINYTEXT
   )
   """
   cursor.execute(create_table_query)

   for _, row in df.iterrows():
      # Periksa apakah data sudah ada di dim_petugas berdasarkan id dan is_current = 1
      check_query = """
      SELECT * FROM dim_penerbit 
      WHERE id = %s
      """
      cursor.execute(check_query, (row['id'],))
      existing_data = cursor.fetchone()

      if existing_data:
         print(f"Data dengan id {row['id']} sudah ada, data akan diskip.")
      else:
         # Jika data belum ada di warehouse, tambahkan data baru
         insert_query = """
         INSERT INTO dim_penerbit (id, nama, telp, alamat)
         VALUES (%s, %s, %s, %s)
         ON DUPLICATE KEY UPDATE
               nama = VALUES(nama),
               telp = VALUES(telp),
               alamat = VALUES(alamat)
         """
         cursor.execute(insert_query, (row['id'], row['nama'], row['telp'], row['alamat']))
         
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
