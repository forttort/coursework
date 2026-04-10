CREATE TABLE general_categories (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE categories (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    general_category_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    CONSTRAINT fk_categories_general_category
        FOREIGN KEY (general_category_id) REFERENCES general_categories(id) ON DELETE RESTRICT,
    CONSTRAINT uq_categories_general_category_name
        UNIQUE (general_category_id, name)
);

CREATE TABLE subcategories (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    CONSTRAINT fk_subcategories_category
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    CONSTRAINT uq_subcategories_category_name
        UNIQUE (category_id, name)
);

CREATE TABLE brands (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE conditions (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(10) NOT NULL UNIQUE
);

CREATE TABLE genders (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE sources (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    base_url VARCHAR(255)
);

CREATE TABLE currencies (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE products (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    brand_id INTEGER,
    gender_id INTEGER,
    subcategory_id INTEGER,
    condition_id INTEGER,
    source_id INTEGER NOT NULL,
    currency_id INTEGER NOT NULL,
    source_product_id VARCHAR(100) NOT NULL,
    size_label VARCHAR(50),
    measurements_text TEXT,
    price_original NUMERIC(12,2),
    price_rub NUMERIC(12,2),
    delivery_estimate VARCHAR(100),
    description TEXT,
    product_url TEXT NOT NULL,
    main_image_url TEXT,
    parsed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_products_brand
        FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE SET NULL,
    CONSTRAINT fk_products_gender
        FOREIGN KEY (gender_id) REFERENCES genders(id) ON DELETE SET NULL,
    CONSTRAINT fk_products_subcategory
        FOREIGN KEY (subcategory_id) REFERENCES subcategories(id) ON DELETE SET NULL,
    CONSTRAINT fk_products_condition
        FOREIGN KEY (condition_id) REFERENCES conditions(id) ON DELETE SET NULL,
    CONSTRAINT fk_products_source
        FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE RESTRICT,
    CONSTRAINT fk_products_currency
        FOREIGN KEY (currency_id) REFERENCES currencies(id) ON DELETE RESTRICT,
    CONSTRAINT uq_products_source_external
        UNIQUE (source_id, source_product_id)
);

CREATE TABLE product_images (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id INTEGER NOT NULL,
    image_url TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 1,

    CONSTRAINT fk_product_images_product
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    CONSTRAINT uq_product_images_product_position
        UNIQUE (product_id, position)
);

CREATE INDEX idx_categories_general_category_id ON categories(general_category_id);
CREATE INDEX idx_subcategories_category_id ON subcategories(category_id);
CREATE INDEX idx_products_brand_id ON products(brand_id);
CREATE INDEX idx_products_gender_id ON products(gender_id);
CREATE INDEX idx_products_subcategory_id ON products(subcategory_id);
CREATE INDEX idx_products_condition_id ON products(condition_id);
CREATE INDEX idx_products_source_id ON products(source_id);
CREATE INDEX idx_products_currency_id ON products(currency_id);
CREATE INDEX idx_product_images_product_id ON product_images(product_id);
