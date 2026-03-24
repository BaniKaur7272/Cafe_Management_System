CREATE TABLE users(
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(120) UNIQUE,
    password VARCHAR(200),
    role VARCHAR(20)
);

CREATE TABLE menu_items(
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(50),
    price INT,
    stock INT,
    image TEXT
);

CREATE TABLE tables(
    id SERIAL PRIMARY KEY,
    table_number INT,
    status VARCHAR(20)
);

CREATE TABLE orders(
    id SERIAL PRIMARY KEY,
    table_number INT,
    total INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);