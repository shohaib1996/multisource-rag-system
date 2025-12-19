-- USERS
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- PRODUCTS
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    stock_quantity INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- ORDERS
-- Order lifecycle only (NOT payment truth)
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    status TEXT CHECK (
        status IN (
            'pending',
            'shipped',
            'delivered',
            'failed',
            'cancelled'
        )
    ) NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    -- IMPORTANT for AI + conversion
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- ORDER ITEMS
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id) ON DELETE CASCADE,
    product_id INT REFERENCES products(id),
    quantity INT NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL
);
-- PAYMENTS
-- Revenue truth lives here
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    provider TEXT NOT NULL,
    transaction_id TEXT UNIQUE,
    payment_method TEXT,
    payment_status TEXT CHECK (
        payment_status IN ('paid', 'failed', 'refunded')
    ) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- (Optional for later – NOT required for Step 4)
-- Cached exchange rates for currency conversion
-- CREATE TABLE exchange_rates (
--     base_currency TEXT NOT NULL,
--     target_currency TEXT NOT NULL,
--     rate NUMERIC(12, 6) NOT NULL,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     PRIMARY KEY (base_currency, target_currency)
-- );