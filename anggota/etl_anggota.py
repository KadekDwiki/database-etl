import mysql.connector
import pandas as pd

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
   query = "SELECT * FROM anggota" 
   df = pd.read_sql(query, conn) 
   return df

# 3. Fungsi untuk mentransformasikan data (Transform)
def transform_data(df):
   df.fillna({'nama': 'Tidak Ada Nama',
            'jenis_kelamin': 'Tidak ingin menjawab',
            'alamat': 'Tidak diketahui',
            'telp': '-'},
            inplace=True)
   
   df['nama'] = df['nama'].str.upper()
   df['alamat'] = df['alamat'].replace(r'^\s*$', 'Tidak Diketahui', regex=True)
   df['jenis_kelamin'] = df['jenis_kelamin'].replace({'P': 'Perempuan',
                                                      'L': 'Laki-laki'})
   
   return df

# 4. Fungsi untuk memuat data (Load)
def load_data_to_staging(conn, df):
   cursor = conn.cursor()

   # Pastikan tabel tujuan sudah ada di database (atau buat tabel baru)
   create_table_query = """
   CREATE TABLE IF NOT EXISTS anggota_transformed (
      id INT PRIMARY KEY,
      nama VARCHAR(255),
      jenis_kelamin VARCHAR(50),
      alamat TINYTEXT,
      telp VARCHAR(12)
   )
   """
   cursor.execute(create_table_query)
   
   # Memasukkan data yang sudah ditransformasikan ke dalam tabel tujuan
   for _, row in df.iterrows():
      insert_query = """
      INSERT INTO anggota_transformed (id, nama, jenis_kelamin, alamat, telp)
      VALUES (%s, %s, %s, %s, %s)
      """
      cursor.execute(insert_query, (row['id'], row['nama'], row['jenis_kelamin'], row['alamat'], row['telp']))

   conn.commit()
   print("Data berhasil dimuat ke dalam database.")

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