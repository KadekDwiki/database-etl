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
   query = "SELECT * FROM fact_peminjaman"
   df = pd.read_sql(query, conn)
   return df

def load_data_to_warehouse(conn, df):
   cursor = conn.cursor()

   # Membuat tabel jika belum ada
   create_table_query = """
   CREATE TABLE IF NOT EXISTS fact_peminjaman (
      fact_id INT AUTO_INCREMENT PRIMARY KEY,
      peminjaman_id INT NOT NULL,
      time_peminjaman_id INT NOT NULL,
      time_kembali_id INT NOT NULL,
      petugas_id INT NOT NULL,
      anggota_id INT NOT NULL,
      total_buku INT NOT NULL,
      FOREIGN KEY (time_peminjaman_id) REFERENCES dim_time(date_id),
      FOREIGN KEY (time_kembali_id) REFERENCES dim_time(date_id)
   );
   """
   cursor.execute(create_table_query)

   for _, row in df.iterrows():
      
      # Periksa apakah data sudah ada di dim_anggota berdasarkan id dan is_current = 1
      check_query = """
      SELECT * FROM fact_peminjaman 
      WHERE fact_id = %s
      """
      cursor.execute(check_query, (row['fact_id'],))
      existing_data = cursor.fetchone()

      if existing_data:
         print(f"Data dengan id {row['fact_id']} sudah ada, data akan diskip.")
      else:
         # Jika data belum ada di warehouse, tambahkan data baru
         insert_query = """
         INSERT INTO fact_peminjaman (peminjaman_id, time_peminjaman_id, time_kembali_id, petugas_id, anggota_id, total_buku)
         VALUES (%s, %s, %s, %s, %s, %s)
         """
         cursor.execute(insert_query, (
         row['peminjaman_id'], 
         row['time_peminjaman_id'], 
         row['time_kembali_id'], 
         row['petugas_id'], 
         row['anggota_id'], 
         row['total_buku']
      ))
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
