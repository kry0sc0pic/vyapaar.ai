-- ==========================================
-- 1. DIMENSION: Products (Restricted to 5)
-- ==========================================
DROP TABLE IF EXISTS sale_items;
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS products;

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name_en VARCHAR(100) NOT NULL,
    name_local VARCHAR(100),
    category VARCHAR(50),
    current_price DECIMAL(10, 2),
    unit VARCHAR(20),
    current_stock INT DEFAULT 0
);

-- ==========================================
-- 2. FACT HEADER: Sales
-- ==========================================
CREATE TABLE sales (
    sale_id SERIAL PRIMARY KEY,
    sale_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) DEFAULT 0.00
);

-- ==========================================
-- 3. FACT DETAILS: Sale Items
-- ==========================================
CREATE TABLE sale_items (
    item_id SERIAL PRIMARY KEY,
    sale_id INT REFERENCES sales(sale_id) ON DELETE CASCADE,
    product_id INT REFERENCES products(product_id),
    quantity INT NOT NULL,
    sold_price DECIMAL(10, 2) NOT NULL
);

-- ==========================================
-- SEED DATA: Inventory (Original 5 items)
-- ==========================================
INSERT INTO products (name_en, name_local, category, current_price, unit, current_stock) VALUES
('Mother Dairy Full Cream', 'Mother Dairy Doodh', 'Dairy', 66.00, 'packet', 50),
('Amul Taaza Milk', 'Amul Doodh', 'Dairy', 54.00, 'packet', 50),
('Farm Fresh Eggs', 'Ande', 'Dairy', 84.00, 'dozen', 100),
('Amul Butter', 'Makhan', 'Dairy', 58.00, '100g', 30),
('Harvest Gold Bread', 'Bread', 'Bakery', 45.00, 'packet', 40);

-- ==========================================
-- GENERATOR: 1 Year History (Fixed 5 Items)
-- ==========================================
DO $$
DECLARE
    i INT;
    j INT;
    
    -- Config
    total_transactions INT := 4000; -- ~11 sales/day
    days_history INT := 365;
    
    -- Helpers
    random_product INT;
    random_qty INT;
    new_sale_id INT;
    sale_total DECIMAL(10,2);
    p_price DECIMAL(10,2);
    
    -- Time Logic
    random_day_offset INT;
    random_hour_offset INT;
BEGIN
    FOR i IN 1..total_transactions LOOP

        -- 1. Generate Time: 0-365 days ago, between 08:00 and 22:00
        random_day_offset := floor(random() * days_history); 
        random_hour_offset := floor(random() * 14) + 8; -- 8 AM to 10 PM

        INSERT INTO sales (sale_time, total_amount)
        VALUES (
            (CURRENT_DATE - (random_day_offset || ' days')::interval) + (random_hour_offset || ' hours')::interval + (floor(random()*60) || ' minutes')::interval,
            0
        ) RETURNING sale_id INTO new_sale_id;

        -- 2. Add Line Items
        sale_total := 0;

        -- Create 1 to 3 items per receipt
        FOR j IN 1..(floor(random() * 3 + 1)::int) LOOP
            
            -- HARDCODED 1-5 (Since we strictly have 5 products and dropped table resets IDs)
            random_product := floor(random() * 5 + 1); 
            random_qty := floor(random() * 3 + 1); 

            SELECT current_price INTO p_price FROM products WHERE product_id = random_product;

            IF p_price IS NOT NULL THEN
                INSERT INTO sale_items (sale_id, product_id, quantity, sold_price)
                VALUES (new_sale_id, random_product, random_qty, p_price);

                sale_total := sale_total + (p_price * random_qty);
            END IF;
        END LOOP;

        -- 3. Update Total
        UPDATE sales SET total_amount = sale_total WHERE sale_id = new_sale_id;

    END LOOP;
END $$;

