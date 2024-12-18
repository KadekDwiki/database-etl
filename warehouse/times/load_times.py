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
   query = "SELECT * FROM dim_time"
   df = pd.read_sql(query, conn) 
   return df

def load_data_to_warehouse(conn, df):
   cursor = conn.cursor()

   # Membuat tabel jika belum ada
   create_table_query = """
   CREATE TABLE IF NOT EXISTS dim_time (
      date_id INT AUTO_INCREMENT PRIMARY KEY,
      full_date DATE NOT NULL,
      day INT NOT NULL,
      day_name VARCHAR(15) NOT NULL,
      week INT NOT NULL,
      month INT NOT NULL,
      month_name VARCHAR(15) NOT NULL,
      year INT NOT NULL
   );
   """
   cursor.execute(create_table_query)

   for _, row in df.iterrows():
      # Periksa apakah data sudah ada di dim_petugas berdasarkan id dan is_current = 1
      check_query = """
      SELECT * FROM dim_time 
      WHERE date_id = %s
      """
      cursor.execute(check_query, (row['date_id'],))
      existing_data = cursor.fetchone()

      if existing_data:
         print(f"Data dengan date_id {row['date_id']} sudah ada, data akan diskip.")
      else:
         # Jika data belum ada di warehouse, tambahkan data baru
         insert_query = """
         INSERT INTO dim_time (date_id, full_date, day, day_name, week, month, month_name, year)
         VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
         ON DUPLICATE KEY UPDATE
               full_date = VALUES(full_date),
               day = VALUES(day),
               day_name = VALUES(day_name),
               week = VALUES(week),
               month = VALUES(month),
               month_name = VALUES(month_name),
               year = VALUES(year)
         """
         cursor.execute(insert_query, (row['date_id'], row['full_date'], row['day'], row['day_name'], row['week'], row['month'], row['month_name'], row['year']))
         
         print(f"Data dengan id {row['date_id']} berhasil ditambahkan ke data warehouse.")

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
