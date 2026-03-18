Run steps:

1. pip install -r requirements.txt
2. create a .env file in the root directory and add:
    SECRET_KEY=your_secret_key 
    DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/cafe_db
3. python app.py
4. open http://127.0.0.1:5000

admin login  admin@cafe.com
password   admin123

staff login staff@cafe.com
password  staff123

customer login  customer@cafe.com
password   cust123
