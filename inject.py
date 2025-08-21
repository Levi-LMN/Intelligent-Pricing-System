# Kenyan Detergent Market Data Injection Script
# This script populates the database with realistic Kenyan detergent products and recipes

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sqlite3

# Initialize Flask app context for database operations
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pricing_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Sample data for Kenyan detergent market
KENYAN_DETERGENT_PRODUCTS = [
    # Laundry Powder Detergents
    {
        'name': 'Omo Advanced Powder',
        'category': 'Laundry Powder',
        'batch_size': 1000.0,  # 1000 units (1kg packs)
        'labor_cost_per_batch': 500.0,
        'overhead_percentage': 18.0,
        'packaging_cost': 150.0,
        'profit_margin_percentage': 30.0,
        'recipe': [
            {'material': 'Linear Alkylbenzene Sulfonate (LAS)', 'percentage': 12.0, 'notes': 'Primary surfactant'},
            {'material': 'Sodium Tripolyphosphate (STPP)', 'percentage': 25.0, 'notes': 'Builder'},
            {'material': 'Sodium Carbonate (Soda Ash)', 'percentage': 15.0, 'notes': 'Alkalinity builder'},
            {'material': 'Zeolite 4A', 'percentage': 20.0, 'notes': 'Water softener'},
            {'material': 'Sodium Sulfate', 'percentage': 20.0, 'notes': 'Filler'},
            {'material': 'Optical Brightening Agent (OBA)', 'percentage': 0.3, 'notes': 'Whitening agent'},
            {'material': 'Protease Enzyme', 'percentage': 0.8, 'notes': 'Protein stain removal'},
            {'material': 'Amylase Enzyme', 'percentage': 0.5, 'notes': 'Starch stain removal'},
            {'material': 'Carboxymethyl Cellulose (CMC)', 'percentage': 1.0, 'notes': 'Anti-redeposition'},
            {'material': 'Lavender Fragrance', 'quantity': 5.0, 'unit': 'ml', 'notes': 'Fragrance'},
            {'material': 'Blue Dye', 'quantity': 2.0, 'unit': 'ml', 'notes': 'Coloring'},
        ]
    },
    {
        'name': 'Ariel Powder Original',
        'category': 'Laundry Powder',
        'batch_size': 500.0,  # 500 units (500g packs)
        'labor_cost_per_batch': 300.0,
        'overhead_percentage': 16.0,
        'packaging_cost': 80.0,
        'profit_margin_percentage': 28.0,
        'recipe': [
            {'material': 'Linear Alkylbenzene Sulfonate (LAS)', 'percentage': 15.0, 'notes': 'Primary surfactant'},
            {'material': 'Sodium Tripolyphosphate (STPP)', 'percentage': 22.0, 'notes': 'Builder'},
            {'material': 'Sodium Carbonate (Soda Ash)', 'percentage': 12.0, 'notes': 'Alkalinity builder'},
            {'material': 'Zeolite 4A', 'percentage': 18.0, 'notes': 'Water softener'},
            {'material': 'Sodium Sulfate', 'percentage': 25.0, 'notes': 'Filler'},
            {'material': 'Protease Enzyme', 'percentage': 1.0, 'notes': 'Stain removal'},
            {'material': 'Lipase Enzyme', 'percentage': 0.6, 'notes': 'Grease removal'},
            {'material': 'Optical Brightening Agent (OBA)', 'percentage': 0.4, 'notes': 'Whitening'},
            {'material': 'Fresh Breeze Fragrance', 'quantity': 3.0, 'unit': 'ml', 'notes': 'Fragrance'},
        ]
    },
    {
        'name': 'Sunlight Powder',
        'category': 'Laundry Powder',
        'batch_size': 2000.0,  # 2000 units (500g packs)
        'labor_cost_per_batch': 400.0,
        'overhead_percentage': 14.0,
        'packaging_cost': 200.0,
        'profit_margin_percentage': 25.0,
        'recipe': [
            {'material': 'Linear Alkylbenzene Sulfonate (LAS)', 'percentage': 10.0, 'notes': 'Primary surfactant'},
            {'material': 'Sodium Tripolyphosphate (STPP)', 'percentage': 28.0, 'notes': 'Builder'},
            {'material': 'Sodium Carbonate (Soda Ash)', 'percentage': 18.0, 'notes': 'Alkalinity'},
            {'material': 'Zeolite 4A', 'percentage': 15.0, 'notes': 'Water softener'},
            {'material': 'Sodium Sulfate', 'percentage': 24.0, 'notes': 'Filler'},
            {'material': 'Protease Enzyme', 'percentage': 0.7, 'notes': 'Enzyme cleaning'},
            {'material': 'Carboxymethyl Cellulose (CMC)', 'percentage': 0.8, 'notes': 'Anti-redeposition'},
            {'material': 'Lemon Fragrance', 'quantity': 4.0, 'unit': 'ml', 'notes': 'Lemon scent'},
        ]
    },

    # Liquid Detergents
    {
        'name': 'Omo Liquid Detergent',
        'category': 'Liquid Detergent',
        'batch_size': 1000.0,  # 1000 bottles (1L each)
        'labor_cost_per_batch': 600.0,
        'overhead_percentage': 20.0,
        'packaging_cost': 250.0,
        'profit_margin_percentage': 35.0,
        'recipe': [
            {'material': 'Sodium Laureth Sulfate (SLES)', 'percentage': 15.0, 'notes': 'Primary surfactant'},
            {'material': 'Cocamidopropyl Betaine', 'percentage': 3.0, 'notes': 'Foam booster'},
            {'material': 'Sodium Tripolyphosphate (STPP)', 'percentage': 8.0, 'notes': 'Builder'},
            {'material': 'Glycerin', 'percentage': 2.0, 'notes': 'Stabilizer'},
            {'material': 'Sodium Chloride (Salt)', 'percentage': 1.5, 'notes': 'Viscosity control'},
            {'material': 'Citric Acid', 'percentage': 0.5, 'notes': 'pH adjustment'},
            {'material': 'Protease Enzyme', 'percentage': 1.2, 'notes': 'Stain removal'},
            {'material': 'Optical Brightening Agent (OBA)', 'percentage': 0.2, 'notes': 'Whitening'},
            {'material': 'Lavender Fragrance', 'quantity': 8.0, 'unit': 'ml', 'notes': 'Fragrance'},
            {'material': 'Blue Dye', 'quantity': 1.5, 'unit': 'ml', 'notes': 'Color'},
        ]
    },
    {
        'name': 'Ariel Liquid Power',
        'category': 'Liquid Detergent',
        'batch_size': 500.0,  # 500 bottles (500ml each)
        'labor_cost_per_batch': 350.0,
        'overhead_percentage': 18.0,
        'packaging_cost': 120.0,
        'profit_margin_percentage': 32.0,
        'recipe': [
            {'material': 'Sodium Laureth Sulfate (SLES)', 'percentage': 18.0, 'notes': 'Primary surfactant'},
            {'material': 'Alpha Olefin Sulfonate (AOS)', 'percentage': 5.0, 'notes': 'Secondary surfactant'},
            {'material': 'Cocamidopropyl Betaine', 'percentage': 4.0, 'notes': 'Foam stabilizer'},
            {'material': 'Sodium Tripolyphosphate (STPP)', 'percentage': 6.0, 'notes': 'Builder'},
            {'material': 'Glycerin', 'percentage': 3.0, 'notes': 'Moisturizer'},
            {'material': 'Protease Enzyme', 'percentage': 1.5, 'notes': 'Protein removal'},
            {'material': 'Lipase Enzyme', 'percentage': 0.8, 'notes': 'Fat removal'},
            {'material': 'Ethylenediaminetetraacetic Acid (EDTA)', 'percentage': 0.3, 'notes': 'Chelating agent'},
            {'material': 'Fresh Breeze Fragrance', 'quantity': 6.0, 'unit': 'ml', 'notes': 'Scent'},
        ]
    },

    # Dishwashing Liquids
    {
        'name': 'Mama Lemon Dishwashing Liquid',
        'category': 'Dishwashing Liquid',
        'batch_size': 1000.0,  # 1000 bottles (400ml each)
        'labor_cost_per_batch': 450.0,
        'overhead_percentage': 16.0,
        'packaging_cost': 180.0,
        'profit_margin_percentage': 40.0,
        'recipe': [
            {'material': 'Sodium Laureth Sulfate (SLES)', 'percentage': 25.0, 'notes': 'High foam surfactant'},
            {'material': 'Cocamidopropyl Betaine', 'percentage': 8.0, 'notes': 'Foam booster'},
            {'material': 'Sodium Dodecyl Sulfate (SDS)', 'percentage': 3.0, 'notes': 'Degreasing agent'},
            {'material': 'Sodium Chloride (Salt)', 'percentage': 2.0, 'notes': 'Viscosity builder'},
            {'material': 'Glycerin', 'percentage': 1.5, 'notes': 'Hand protection'},
            {'material': 'Citric Acid', 'percentage': 0.8, 'notes': 'pH control'},
            {'material': 'Ethylenediaminetetraacetic Acid (EDTA)', 'percentage': 0.2, 'notes': 'Water softener'},
            {'material': 'Lemon Fragrance', 'quantity': 10.0, 'unit': 'ml', 'notes': 'Lemon scent'},
            {'material': 'Green Dye', 'quantity': 2.0, 'unit': 'ml', 'notes': 'Green color'},
        ]
    },
    {
        'name': 'Joy Dishwashing Liquid',
        'category': 'Dishwashing Liquid',
        'batch_size': 800.0,  # 800 bottles (200ml each)
        'labor_cost_per_batch': 320.0,
        'overhead_percentage': 15.0,
        'packaging_cost': 95.0,
        'profit_margin_percentage': 38.0,
        'recipe': [
            {'material': 'Sodium Laureth Sulfate (SLES)', 'percentage': 22.0, 'notes': 'Primary surfactant'},
            {'material': 'Cocamidopropyl Betaine', 'percentage': 6.0, 'notes': 'Mild surfactant'},
            {'material': 'Sodium Chloride (Salt)', 'percentage': 2.5, 'notes': 'Thickener'},
            {'material': 'Glycerin', 'percentage': 2.0, 'notes': 'Skin care'},
            {'material': 'Citric Acid', 'percentage': 0.6, 'notes': 'Preservative'},
            {'material': 'Lemon Fragrance', 'quantity': 8.0, 'unit': 'ml', 'notes': 'Citrus scent'},
        ]
    },

    # Bar Soaps
    {
        'name': 'Sunlight Bar Soap',
        'category': 'Laundry Bar Soap',
        'batch_size': 2000.0,  # 2000 bars (200g each)
        'labor_cost_per_batch': 800.0,
        'overhead_percentage': 12.0,
        'packaging_cost': 300.0,
        'profit_margin_percentage': 25.0,
        'recipe': [
            {'material': 'Palm Kernel Oil', 'percentage': 45.0, 'notes': 'Base oil'},
            {'material': 'Coconut Oil', 'percentage': 25.0, 'notes': 'Lathering agent'},
            {'material': 'Palm Oil', 'percentage': 20.0, 'notes': 'Hardness'},
            {'material': 'Sodium Hydroxide (Caustic Soda)', 'percentage': 6.0, 'notes': 'Saponification'},
            {'material': 'Sodium Chloride (Salt)', 'percentage': 2.0, 'notes': 'Hardener'},
            {'material': 'Glycerin', 'percentage': 1.0, 'notes': 'Moisturizer'},
            {'material': 'Lemon Fragrance', 'quantity': 15.0, 'unit': 'ml', 'notes': 'Scent'},
        ]
    },
    {
        'name': 'Kiwi Laundry Soap',
        'category': 'Laundry Bar Soap',
        'batch_size': 1500.0,  # 1500 bars (250g each)
        'labor_cost_per_batch': 650.0,
        'overhead_percentage': 14.0,
        'packaging_cost': 225.0,
        'profit_margin_percentage': 22.0,
        'recipe': [
            {'material': 'Palm Oil', 'percentage': 40.0, 'notes': 'Primary fat'},
            {'material': 'Coconut Oil', 'percentage': 30.0, 'notes': 'Foam generation'},
            {'material': 'Palm Kernel Oil', 'percentage': 20.0, 'notes': 'Cleaning power'},
            {'material': 'Sodium Hydroxide (Caustic Soda)', 'percentage': 7.0, 'notes': 'Saponification'},
            {'material': 'Sodium Carbonate (Soda Ash)', 'percentage': 2.0, 'notes': 'Alkalinity'},
            {'material': 'Fresh Breeze Fragrance', 'quantity': 12.0, 'unit': 'ml', 'notes': 'Fresh scent'},
        ]
    },

    # Multipurpose Cleaners
    {
        'name': 'Vim Multipurpose Cleaner',
        'category': 'Multipurpose Cleaner',
        'batch_size': 600.0,  # 600 bottles (500ml each)
        'labor_cost_per_batch': 280.0,
        'overhead_percentage': 17.0,
        'packaging_cost': 105.0,
        'profit_margin_percentage': 35.0,
        'recipe': [
            {'material': 'Sodium Laureth Sulfate (SLES)', 'percentage': 12.0, 'notes': 'Cleaning agent'},
            {'material': 'Sodium Tripolyphosphate (STPP)', 'percentage': 5.0, 'notes': 'Degreaser'},
            {'material': 'Citric Acid', 'percentage': 3.0, 'notes': 'Lime scale removal'},
            {'material': 'Sodium Hypochlorite', 'percentage': 2.0, 'notes': 'Disinfectant'},
            {'material': 'Sodium Chloride (Salt)', 'percentage': 1.0, 'notes': 'Thickener'},
            {'material': 'Lemon Fragrance', 'quantity': 5.0, 'unit': 'ml', 'notes': 'Fresh scent'},
        ]
    },
    {
        'name': 'Jik Toilet Cleaner',
        'category': 'Toilet Cleaner',
        'batch_size': 1000.0,  # 1000 bottles (750ml each)
        'labor_cost_per_batch': 400.0,
        'overhead_percentage': 15.0,
        'packaging_cost': 150.0,
        'profit_margin_percentage': 30.0,
        'recipe': [
            {'material': 'Sodium Hypochlorite', 'percentage': 5.0, 'notes': 'Active bleach'},
            {'material': 'Sodium Hydroxide (Caustic Soda)', 'percentage': 1.0, 'notes': 'pH adjustment'},
            {'material': 'Sodium Chloride (Salt)', 'percentage': 0.5, 'notes': 'Stabilizer'},
            {'material': 'Fresh Breeze Fragrance', 'quantity': 3.0, 'unit': 'ml', 'notes': 'Masking scent'},
        ]
    },
]


def create_sample_data():
    """Create sample detergent products and recipes for Kenyan market"""

    with app.app_context():
        try:
            print("🧼 Creating Kenyan detergent market sample data...")
            print("=" * 60)

            # Get material IDs mapping
            materials = {}
            conn = sqlite3.connect('pricing_system.db')
            cursor = conn.cursor()

            cursor.execute("SELECT id, name FROM raw_material")
            for material_id, name in cursor.fetchall():
                materials[name] = material_id

            conn.close()

            products_created = 0
            recipes_created = 0

            for product_data in KENYAN_DETERGENT_PRODUCTS:
                try:
                    # Create product
                    cursor = sqlite3.connect('pricing_system.db').cursor()

                    cursor.execute("""
                        INSERT INTO product (name, category, batch_size, labor_cost_per_batch, 
                                           overhead_percentage, packaging_cost, profit_margin_percentage, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        product_data['name'],
                        product_data['category'],
                        product_data['batch_size'],
                        product_data['labor_cost_per_batch'],
                        product_data['overhead_percentage'],
                        product_data['packaging_cost'],
                        product_data['profit_margin_percentage'],
                        datetime.now()
                    ))

                    product_id = cursor.lastrowid
                    cursor.connection.commit()
                    products_created += 1

                    print(f"✓ Created product: {product_data['name']}")

                    # Create recipes
                    for recipe_item in product_data['recipe']:
                        material_name = recipe_item['material']

                        if material_name not in materials:
                            print(f"  ⚠️  Material '{material_name}' not found in database")
                            continue

                        material_id = materials[material_name]
                        notes = recipe_item.get('notes', '')

                        # Handle percentage vs absolute quantities
                        if 'percentage' in recipe_item:
                            # Percentage-based recipe
                            percentage_value = recipe_item['percentage']
                            is_percentage_based = True

                            # Calculate absolute quantity based on batch size and material type
                            cursor.execute("SELECT unit FROM raw_material WHERE id = ?", (material_id,))
                            unit = cursor.fetchone()[0]

                            batch_size = product_data['batch_size']

                            if unit == 'kg':
                                # Assume 20g per unit for powder products, 1kg per unit for liquid
                                if 'Liquid' in product_data['category']:
                                    estimated_batch_weight = batch_size * 1.0  # 1kg per liter
                                else:
                                    estimated_batch_weight = batch_size * 0.02  # 20g per unit
                                actual_quantity = (percentage_value / 100) * estimated_batch_weight
                            elif unit in ['ml', 'L']:
                                # For liquids and fragrances
                                if unit == 'L':
                                    actual_quantity = (percentage_value / 100) * batch_size * 0.001
                                else:
                                    actual_quantity = (percentage_value / 100) * batch_size
                            else:
                                # For pieces
                                actual_quantity = (percentage_value / 100) * batch_size

                        else:
                            # Absolute quantity
                            actual_quantity = recipe_item['quantity']
                            percentage_value = None
                            is_percentage_based = False

                        # Insert recipe
                        cursor.execute("""
                            INSERT INTO recipe (product_id, material_id, quantity_per_batch, 
                                              is_percentage_based, percentage_value, notes, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            product_id,
                            material_id,
                            actual_quantity,
                            is_percentage_based,
                            percentage_value,
                            notes,
                            datetime.now(),
                            datetime.now()
                        ))

                        recipes_created += 1

                        if is_percentage_based:
                            print(f"  + {material_name}: {percentage_value}% ({actual_quantity:.3f} {unit}) - {notes}")
                        else:
                            print(f"  + {material_name}: {actual_quantity} - {notes}")

                    cursor.connection.commit()
                    cursor.connection.close()
                    print()

                except Exception as e:
                    print(f"❌ Error creating product {product_data['name']}: {e}")
                    continue

            print("=" * 60)
            print(f"🎉 Successfully created {products_created} products with {recipes_created} recipe items!")
            print("\nProducts created:")
            for product in KENYAN_DETERGENT_PRODUCTS:
                print(f"  • {product['name']} ({product['category']})")

            print(f"\n💡 These products represent common detergent formulations in the Kenyan market.")
            print(f"📊 You can now use the cost analysis features to calculate pricing for these products.")

        except Exception as e:
            print(f"❌ Error during data creation: {e}")


def verify_materials():
    """Verify that all required materials exist in the database"""
    required_materials = set()

    for product in KENYAN_DETERGENT_PRODUCTS:
        for recipe_item in product['recipe']:
            required_materials.add(recipe_item['material'])

    conn = sqlite3.connect('pricing_system.db')
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM raw_material")
    existing_materials = {row[0] for row in cursor.fetchall()}
    conn.close()

    missing_materials = required_materials - existing_materials

    if missing_materials:
        print("⚠️  Missing materials in database:")
        for material in sorted(missing_materials):
            print(f"  • {material}")
        print(f"\nPlease add these materials to your database first.")
        return False
    else:
        print("✅ All required materials are available in the database!")
        return True


if __name__ == '__main__':
    print("🧼 Kenyan Detergent Market Data Injection")
    print("=" * 50)

    # Verify materials first
    if verify_materials():
        print("\n🚀 Starting data injection...")
        create_sample_data()
    else:
        print("\n❌ Cannot proceed without required materials.")
        print("Run the materials setup script first, or add the missing materials manually.")