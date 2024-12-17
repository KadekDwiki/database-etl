import mysql.connector
import pandas as pd
from datetime import datetime, timedelta

# Fungsi koneksi ke database sumber
def create_source_connection():
   conn = mysql.connector.connect(
      host='localhost',
      user='root',
      password='',
      database='db_perpustakaan'  # Database sumber
   )
   return conn

# Fungsi koneksi ke database staging
def create_staging_connection():
   conn = mysql.connector.connect(
      host='localhost',
      user='root',
      password='',
      database='db_perpustakaan_staging'  # Database staging
   )
   return conn

# Fungsi untuk membuat tabel fakta pengembalian dengan foreign key ke dimensi waktu
def create_fact_pengembalian_table_with_time():
   conn = create_staging_connection()
   cursor = conn.cursor()

   create_table_query = """
   CREATE TABLE IF NOT EXISTS fact_pengembalian (
      fact_id INT AUTO_INCREMENT PRIMARY KEY,
      pengembalian_id INT NOT NULL,
      time_pengembalian_id INT NOT NULL,
      petugas_id INT NOT NULL,
      anggota_id INT NOT NULL,
      total_buku INT NOT NULL,
      total_denda DECIMAL(10,2) NOT NULL,
      FOREIGN KEY (time_pengembalian_id) REFERENCES dim_time(date_id)
   );
   """
   cursor.execute(create_table_query)
   conn.commit()
   cursor.close()
   conn.close()
   print("Tabel fact_pengembalian berhasil dibuat dengan dimensi waktu.")

# Fungsi untuk menghitung total pengembalian buku dan denda dari database sumber
def calculate_total_pengembalian():
   conn = create_source_connection()

   # Query untuk menghitung total buku yang dikembalikan dan total denda per pengembalian_id
   query = """
   SELECT 
      p.id AS pengembalian_id,
      p.tanggal_pengembalian,
      SUM(p.denda) AS total_denda,
      p.petugas_id,
      p.anggota_id,
      COUNT(pd.buku_id) AS total_buku
   FROM 
      pengembalian p
   JOIN 
      pengembalian_detail pd ON p.id = pd.pengembalian_id
   GROUP BY 
      p.id, p.tanggal_pengembalian, p.denda, p.petugas_id, p.anggota_id;
   """
   
   # Eksekusi query dan ambil hasilnya ke Pandas DataFrame
   df = pd.read_sql(query, conn)
   conn.close()
   return df

def is_data_exists(pengembalian_id):
   conn = create_staging_connection()
   cursor = conn.cursor()
   cursor.execute("SELECT COUNT(*) FROM fact_pengembalian WHERE pengembalian_id = %s", (pengembalian_id,))
   result = cursor.fetchone()
   conn.close()
   return result[0] > 0

# Fungsi untuk memasukkan data ke tabel fakta pengembalian dengan dimensi waktu
def load_data_to_fact_pengembalian(df):
   conn = create_staging_connection()
   cursor = conn.cursor()

   # Query untuk mendapatkan time_id berdasarkan tanggal
   def get_time_id(date):
      query = "SELECT date_id FROM dim_time WHERE full_date = %s"
      cursor.execute(query, (date,))
      result = cursor.fetchone()
      return result[0] if result else None

   insert_query = """
   INSERT INTO fact_pengembalian (pengembalian_id, time_pengembalian_id, petugas_id, anggota_id, total_buku, total_denda)
   VALUES (%s, %s, %s, %s, %s, %s)
   """

   for _, row in df.iterrows():
      if pd.isnull(row['tanggal_pengembalian']):
         row['tanggal_pengembalian'] = datetime.now()
      
      time_pengembalian_id = get_time_id(row['tanggal_pengembalian'])
      
      if time_pengembalian_id is None:
            print(f"Skipping pengembalian_id {row['pengembalian_id']} due to invalid date.")
            continue
         
      if is_data_exists(row['pengembalian_id']):
         print(f"Skipping pengembalian_id {row['pengembalian_id']} karena sudah ada.")
         continue

      cursor.execute(insert_query, (
         row['pengembalian_id'], 
         time_pengembalian_id, 
         row['petugas_id'], 
         row['anggota_id'], 
         row['total_buku'], 
         row['total_denda']
      ))

   conn.commit()
   cursor.close()
   conn.close()
   print("Data berhasil dimuat ke tabel fact_pengembalian dengan dimensi waktu.")

# Main function untuk menjalankan semua proses
def main():
   # Membuat tabel fakta di database staging
   create_fact_pengembalian_table_with_time()

   # Menghitung total buku yang dikembalikan dan total denda dari database sumber
   fact_data = calculate_total_pengembalian()
   print("Contoh data yang akan dimuat ke tabel fakta:")
   print(fact_data.head())

   # Memuat data ke tabel fakta di database staging
   load_data_to_fact_pengembalian(fact_data)

   print("Proses selesai: Data berhasil dimuat ke tabel fact_pengembalian di database staging.")

if __name__ == "__main__":
   main()
