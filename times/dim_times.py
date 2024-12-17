import mysql.connector
import pandas as pd
from datetime import datetime, timedelta

# Fungsi koneksi ke database MySQL
def create_connection():
   conn = mysql.connector.connect(
      host='localhost',  
      user='root',          
      password='',          
      database='db_perpustakaan_staging' 
   )
   return conn

# Fungsi untuk membuat tabel dimensi waktu di database
def create_time_dimension_table():
   conn = create_connection()
   cursor = conn.cursor()

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
   conn.commit()
   cursor.close()
   conn.close()
   print("Tabel dim_time berhasil dibuat.")

# Fungsi untuk menghasilkan data dimensi waktu
def generate_time_dimension_data(start_date, end_date):
   date_list = []
   current_date = start_date

   while current_date <= end_date:
      date_list.append({
         'full_date': current_date,
         'day': current_date.day,
         'day_name': current_date.strftime('%A'), 
         'week': current_date.isocalendar()[1],
         'month': current_date.month, 
         'month_name': current_date.strftime('%B'),
         'year': current_date.year 
      })
      current_date += timedelta(days=1)
   
   return pd.DataFrame(date_list)

# Fungsi untuk memasukkan data dimensi waktu ke dalam database
def load_time_dimension_to_db(df):
   conn = create_connection()
   cursor = conn.cursor()

   insert_query = """
   INSERT INTO dim_time (full_date, day, day_name, week, month, month_name, year)
   VALUES (%s, %s, %s, %s, %s, %s, %s)
   """

   for _, row in df.iterrows():
      cursor.execute(insert_query, (
         row['full_date'], row['day'], row['day_name'], row['week'],
         row['month'], row['month_name'], row['year']
      ))
   
   conn.commit()
   cursor.close()
   conn.close()
   print("Data dimensi waktu berhasil dimuat ke database.")

# Main function untuk menjalankan semua proses
def main():
   # Rentang waktu yang diinginkan
   start_date = datetime(2018, 1, 1)
   end_date = datetime(2024, 12, 31)

   # Buat tabel dim_time
   create_time_dimension_table()

   # Generate data dimensi waktu
   time_df = generate_time_dimension_data(start_date, end_date)
   print("Contoh data dimensi waktu:")
   print(time_df.head())

   # Load data ke database
   load_time_dimension_to_db(time_df)

   print("Proses selesai: Tabel dimensi waktu berhasil dibuat dan diisi.")

if __name__ == "__main__":
   main()
