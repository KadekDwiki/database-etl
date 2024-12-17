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
   query = "SELECT * FROM penerbit" 
   df = pd.read_sql(query, conn) 
   return df

# 3. Fungsi untuk mentransformasikan data (Transform)
def transform_data(df):
   df['nama'] = df['nama'].replace(r'^\s*$', None, regex=True)
   df['alamat'] = df['alamat'].replace(r'^\s*$', None, regex=True)
   df['telp'] = df['telp'].replace(r'^\s*$', None, regex=True)
   
   df.fillna({
            'nama': 'Tidak diketahui',
            'alamat': 'Tidka diketahui',
            'telp': '-'
            },
            inplace=True)
   return df

# 4. Fungsi untuk memuat data ke staging area (Load)
def load_data_to_staging(conn, df):
   cursor = conn.cursor()

   create_table_query = """
   CREATE TABLE IF NOT EXISTS penerbit_transformed (
      id INT PRIMARY KEY,
      nama VARCHAR(255),
      telp VARCHAR(12),
      alamat TINYTEXT
   )
   """
   cursor.execute(create_table_query)
   
   # Memasukkan data yang sudah ditransformasikan ke dalam tabel tujuan di staging area
   for _, row in df.iterrows():
      insert_query = """
      INSERT INTO penerbit_transformed (id, nama, telp, alamat)
      VALUES (%s, %s, %s, %s)
      ON DUPLICATE KEY UPDATE
            nama = VALUES(nama),
            telp = VALUES(telp),
            alamat = VALUES(alamat)
      """
      cursor.execute(insert_query, (row['id'], row['nama'], row['telp'], row['alamat']))

   conn.commit()
   print("Data berhasil dimuat ke dalam database dengan SCD Type 1.")

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