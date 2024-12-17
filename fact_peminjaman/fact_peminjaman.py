import mysql.connector
import pandas as pd
from datetime import datetime, timedelta

# Fungsi koneksi ke database sumber
def create_source_connection():
   conn = mysql.connector.connect(
      host='localhost',     
      user='root',          
      password='',          
      database='db_perpustakaan' 
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

# Fungsi untuk membuat tabel fakta peminjaman dengan foreign key ke dimensi waktu
def create_fact_peminjaman_table_with_time():
   conn = create_staging_connection()
   cursor = conn.cursor()

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
   conn.commit()
   cursor.close()
   conn.close()
   print("Tabel fact_peminjaman berhasil dibuat dengan dimensi waktu.")



# Fungsi untuk menghitung total peminjaman buku dari database sumber
def calculate_total_peminjaman():
   conn = create_source_connection()

   # Query untuk menjumlahkan total buku per peminjaman_id
   query = """
   SELECT 
      p.id AS peminjaman_id,
      p.tanggal_pinjam,
      p.tanggal_kembali,
      p.petugas_id,
      p.anggota_id,
      COUNT(pd.buku_id) AS total_buku
   FROM 
      peminjaman p
   JOIN 
      peminjaman_detail pd ON p.id = pd.peminjaman_id
   GROUP BY 
      p.id, p.tanggal_pinjam, p.tanggal_kembali, p.petugas_id, p.anggota_id;
   """
   
   # Eksekusi query dan ambil hasilnya ke Pandas DataFrame
   df = pd.read_sql(query, conn)
   conn.close()
   return df

def is_data_exists(cursor, peminjaman_id, time_peminjaman_id, time_kembali_id):
   query = """
   SELECT COUNT(*) FROM fact_peminjaman
   WHERE peminjaman_id = %s AND time_peminjaman_id = %s AND time_kembali_id = %s
   """
   cursor.execute(query, (peminjaman_id, time_peminjaman_id, time_kembali_id))
   result = cursor.fetchone()
   return result[0] > 0

# Fungsi untuk memasukkan data ke tabel fakta peminjaman dengan dimensi waktu
def load_data_to_fact_peminjaman(df):
   conn = create_staging_connection()
   cursor = conn.cursor()

   # Query untuk mendapatkan time_id berdasarkan tanggal
   def get_time_id(date):
      query = "SELECT date_id FROM dim_time WHERE full_date = %s"
      cursor.execute(query, (date,))
      result = cursor.fetchone()
      return result[0] if result else None

   insert_query = """
   INSERT INTO fact_peminjaman (peminjaman_id, time_peminjaman_id, time_kembali_id, petugas_id, anggota_id, total_buku)
   VALUES (%s, %s, %s, %s, %s, %s)
   """

   for _, row in df.iterrows():
      if pd.isnull(row['tanggal_pinjam']):
         row['tanggal_pinjam'] = datetime.now()

      if pd.isnull(row['tanggal_kembali']):
         row['tanggal_kembali'] = row['tanggal_pinjam'] + timedelta(days=7)

      
      time_peminjaman_id = get_time_id(row['tanggal_pinjam'])
      time_kembali_id = get_time_id(row['tanggal_kembali'])
      
      if time_peminjaman_id is None or time_kembali_id is None:
            print(f"Skipping peminjaman_id {row['peminjaman_id']} due to invalid date.")
            continue
         
      # Mengecek apakah data sudah ada di tabel fakta
      if is_data_exists(cursor, row['peminjaman_id'], time_peminjaman_id, time_kembali_id):
         print(f"Skipping peminjaman_id {row['peminjaman_id']} karena sudah ada.")
         continue 

      cursor.execute(insert_query, (
         row['peminjaman_id'], 
         time_peminjaman_id, 
         time_kembali_id, 
         row['petugas_id'], 
         row['anggota_id'], 
         row['total_buku']
      ))

   conn.commit()
   cursor.close()
   conn.close()
   print("Data berhasil dimuat ke tabel fact_peminjaman dengan dimensi waktu.")

# Main function untuk menjalankan semua proses
def main():
   # Membuat tabel fakta di database staging
   create_fact_peminjaman_table_with_time()

   # Menghitung total buku yang dipinjam dari database sumber
   fact_data = calculate_total_peminjaman()
   print("Contoh data yang akan dimuat ke tabel fakta:")
   print(fact_data.head())

   # Memuat data ke tabel fakta di database staging
   load_data_to_fact_peminjaman(fact_data)

   print("Proses selesai: Data berhasil dimuat ke tabel fact_peminjaman di database staging.")

if __name__ == "__main__":
   main()
