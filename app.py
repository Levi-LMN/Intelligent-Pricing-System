from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import time
import random
from dataclasses import dataclass
from typing import List, Dict, Optional
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pricing_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Database Models
class RawMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), nullable=False)  # kg, liters, pieces
    current_price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Float, default=0)
    minimum_stock = db.Column(db.Float, default=0)
    supplier = db.Column(db.String(100))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    batch_size = db.Column(db.Float, nullable=False)  # Standard batch size
    labor_cost_per_batch = db.Column(db.Float, default=0)
    overhead_percentage = db.Column(db.Float, default=15.0)  # As percentage
    packaging_cost = db.Column(db.Float, default=0)
    profit_margin_percentage = db.Column(db.Float, default=25.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Updated Recipe Model - Replace the existing Recipe class in your app.py

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('raw_material.id'), nullable=False)
    quantity_per_batch = db.Column(db.Float, nullable=False)

    # New columns for percentage support
    is_percentage_based = db.Column(db.Boolean, default=False, nullable=False)
    percentage_value = db.Column(db.Float)  # Store original percentage if applicable
    notes = db.Column(db.String(200))  # Optional notes about the ingredient
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = db.relationship('Product', backref='recipes')
    material = db.relationship('RawMaterial', backref='recipes')

    def __repr__(self):
        return f'<Recipe {self.material.name}: {self.quantity_per_batch}>'

    def get_display_quantity(self):
        """Return formatted display quantity with percentage if applicable"""
        if self.is_percentage_based and self.percentage_value:
            return f"{self.quantity_per_batch:.3f} ({self.percentage_value}%)"
        return f"{self.quantity_per_batch:.3f}"



class MarketPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    competitor = db.Column(db.String(100))
    price = db.Column(db.Float, nullable=False)
    url = db.Column(db.String(500))
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)
    size_info = db.Column(db.String(100))  # e.g., "1kg", "500ml"


class CostAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    batch_size = db.Column(db.Float, nullable=False)
    material_cost = db.Column(db.Float, nullable=False)
    labor_cost = db.Column(db.Float, nullable=False)
    overhead_cost = db.Column(db.Float, nullable=False)
    packaging_cost = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    recommended_price = db.Column(db.Float, nullable=False)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', backref='cost_analyses')


# Market Scraper Class
class MarketScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def scrape_jumia_prices(self, search_term: str, max_results: int = 10) -> List[Dict]:
        """Scrape product prices from Jumia"""
        try:
            search_url = f"https://www.jumia.co.ke/catalog/?q={search_term.replace(' ', '+')}"
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            products = []

            # Find product containers (adjust selectors based on actual Jumia structure)
            product_cards = soup.find_all('article', class_='prd', limit=max_results)

            for card in product_cards:
                try:
                    name_elem = card.find('h3', class_='name')
                    price_elem = card.find('div', class_='prc')
                    link_elem = card.find('a')

                    if name_elem and price_elem:
                        name = name_elem.get_text().strip()
                        price_text = price_elem.get_text().strip()

                        # Extract price number
                        price_match = re.search(r'KSh\s*([\d,]+)', price_text)
                        if price_match:
                            price = float(price_match.group(1).replace(',', ''))
                            url = urljoin('https://www.jumia.co.ke', link_elem.get('href', '')) if link_elem else ''

                            products.append({
                                'name': name,
                                'price': price,
                                'url': url,
                                'competitor': 'Jumia',
                                'size_info': self._extract_size_info(name)
                            })
                except Exception as e:
                    continue

            return products

        except Exception as e:
            print(f"Error scraping Jumia: {e}")
            return []

    def _extract_size_info(self, product_name: str) -> str:
        """Extract size information from product name"""
        size_patterns = [
            r'(\d+(?:\.\d+)?\s*(?:kg|KG|g|G|ml|ML|l|L))',
            r'(\d+(?:\.\d+)?\s*(?:litre|liter|gram)s?)'
        ]

        for pattern in size_patterns:
            match = re.search(pattern, product_name, re.IGNORECASE)
            if match:
                return match.group(1)

        return 'Unknown'


# Helper Functions

def check_stock_availability(product_id: int, batch_size: float) -> Dict:
    """Check if sufficient stock is available for production"""
    product = Product.query.get_or_404(product_id)
    scale_factor = batch_size / product.batch_size

    availability = {
        'can_produce': True,
        'missing_materials': [],
        'low_stock_materials': []
    }

    for recipe in product.recipes:
        required_quantity = recipe.quantity_per_batch * scale_factor
        material = recipe.material

        if material.stock_quantity < required_quantity:
            availability['can_produce'] = False
            availability['missing_materials'].append({
                'material': material.name,
                'required': required_quantity,
                'available': material.stock_quantity,
                'shortage': required_quantity - material.stock_quantity
            })
        elif material.stock_quantity <= material.minimum_stock:
            availability['low_stock_materials'].append({
                'material': material.name,
                'current_stock': material.stock_quantity,
                'minimum_stock': material.minimum_stock
            })

    return availability


# Routes
@app.route('/')
def dashboard():
    total_products = Product.query.count()
    total_materials = RawMaterial.query.count()
    low_stock_materials = RawMaterial.query.filter(
        RawMaterial.stock_quantity <= RawMaterial.minimum_stock
    ).count()

    recent_analyses = CostAnalysis.query.order_by(
        CostAnalysis.calculated_at.desc()
    ).limit(5).all()

    recent_market_data = MarketPrice.query.order_by(
        MarketPrice.scraped_at.desc()
    ).limit(5).all()

    return render_template('dashboard.html',
                           total_products=total_products,
                           total_materials=total_materials,
                           low_stock_materials=low_stock_materials,
                           recent_analyses=recent_analyses,
                           recent_market_data=recent_market_data)


@app.route('/materials')
def materials():
    materials = RawMaterial.query.all()
    return render_template('materials.html', materials=materials)


@app.route('/materials/add', methods=['GET', 'POST'])
def add_material():
    if request.method == 'POST':
        material = RawMaterial(
            name=request.form['name'],
            unit=request.form['unit'],
            current_price=float(request.form['current_price']),
            stock_quantity=float(request.form.get('stock_quantity', 0)),
            minimum_stock=float(request.form.get('minimum_stock', 0)),
            supplier=request.form.get('supplier', '')
        )
        db.session.add(material)
        db.session.commit()
        flash('Material added successfully!', 'success')
        return redirect(url_for('materials'))

    return render_template('add_material.html')


@app.route('/products')
def products():
    products = Product.query.all()
    return render_template('products.html', products=products)


@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product = Product(
            name=request.form['name'],
            category=request.form.get('category', ''),
            batch_size=float(request.form['batch_size']),
            labor_cost_per_batch=float(request.form.get('labor_cost_per_batch', 0)),
            overhead_percentage=float(request.form.get('overhead_percentage', 15)),
            packaging_cost=float(request.form.get('packaging_cost', 0)),
            profit_margin_percentage=float(request.form.get('profit_margin_percentage', 25))
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('products'))

    return render_template('add_product.html')


@app.route('/products/<int:product_id>/recipe')
def product_recipe(product_id):
    product = Product.query.get_or_404(product_id)
    materials = RawMaterial.query.all()
    return render_template('product_recipe.html', product=product, materials=materials)


# Updated add_recipe_item route
@app.route('/products/<int:product_id>/recipe/add', methods=['POST'])
def add_recipe_item(product_id):
    material_id = request.form['material_id']
    quantity_type = request.form.get('quantity_type', 'absolute')
    notes = request.form.get('notes', '')

    # Handle percentage vs absolute quantities
    if quantity_type == 'percentage':
        quantity = float(request.form['actual_quantity'])
        percentage_value = float(request.form['percentage_value'])
        is_percentage_based = True
    else:
        quantity = float(request.form['quantity'])
        percentage_value = None
        is_percentage_based = False

    # Check if recipe item already exists
    existing = Recipe.query.filter_by(
        product_id=product_id,
        material_id=material_id
    ).first()

    if existing:
        existing.quantity_per_batch = quantity
        existing.is_percentage_based = is_percentage_based
        existing.percentage_value = percentage_value
        existing.notes = notes
        existing.updated_at = datetime.utcnow()
        flash('Recipe item updated successfully!', 'success')
    else:
        recipe = Recipe(
            product_id=product_id,
            material_id=material_id,
            quantity_per_batch=quantity,
            is_percentage_based=is_percentage_based,
            percentage_value=percentage_value,
            notes=notes
        )
        db.session.add(recipe)
        flash('Recipe item added successfully!', 'success')

    db.session.commit()
    return redirect(url_for('product_recipe', product_id=product_id))


# Helper function to calculate percentage from absolute quantity
def calculate_percentage_from_absolute(recipe, product):
    """Calculate what percentage an absolute quantity represents"""
    if not recipe.is_percentage_based:
        # Estimate percentage for display purposes
        batch_size = product.batch_size
        material = recipe.material

        if material.unit == 'kg':
            # Assume 20g per unit as default batch weight
            estimated_batch_weight = batch_size * 0.02
            if estimated_batch_weight > 0:
                return (recipe.quantity_per_batch / estimated_batch_weight) * 100
        elif material.unit in ['ml', 'L']:
            # For liquids, calculate based on volume
            batch_volume = batch_size * (0.001 if material.unit == 'L' else 1)
            if batch_volume > 0:
                return (recipe.quantity_per_batch / batch_volume) * 100
        else:
            # For pieces
            if batch_size > 0:
                return (recipe.quantity_per_batch / batch_size) * 100

    return recipe.percentage_value


# Enhanced cost calculation function
def calculate_product_cost(product_id: int, custom_batch_size: Optional[float] = None) -> Dict:
    """Calculate comprehensive cost for a product with percentage support"""
    product = Product.query.get_or_404(product_id)
    batch_size = custom_batch_size or product.batch_size
    scale_factor = batch_size / product.batch_size

    # Calculate material costs
    material_cost = 0
    material_details = []

    for recipe in product.recipes:
        # Scale quantity appropriately
        if recipe.is_percentage_based and recipe.percentage_value:
            # Recalculate percentage-based quantities for the new batch size
            if recipe.material.unit == 'kg':
                estimated_batch_weight = batch_size * 0.02  # 20g per unit
                scaled_quantity = (recipe.percentage_value / 100) * estimated_batch_weight
            elif recipe.material.unit in ['ml', 'L']:
                batch_volume = batch_size * (0.001 if recipe.material.unit == 'L' else 1)
                scaled_quantity = (recipe.percentage_value / 100) * batch_volume
            else:
                scaled_quantity = (recipe.percentage_value / 100) * batch_size
        else:
            # Standard scaling for absolute quantities
            scaled_quantity = recipe.quantity_per_batch * scale_factor

        cost = scaled_quantity * recipe.material.current_price
        material_cost += cost

        material_details.append({
            'material': recipe.material.name,
            'quantity': scaled_quantity,
            'original_quantity': recipe.quantity_per_batch,
            'is_percentage': recipe.is_percentage_based,
            'percentage_value': recipe.percentage_value,
            'unit': recipe.material.unit,
            'unit_price': recipe.material.current_price,
            'total_cost': cost,
            'notes': recipe.notes
        })

    # Calculate other costs (same as before)
    labor_cost = product.labor_cost_per_batch * scale_factor
    overhead_cost = material_cost * (product.overhead_percentage / 100)
    packaging_cost = product.packaging_cost * scale_factor

    total_cost = material_cost + labor_cost + overhead_cost + packaging_cost
    recommended_price = total_cost * (1 + product.profit_margin_percentage / 100)

    return {
        'product': product,
        'batch_size': batch_size,
        'material_cost': material_cost,
        'labor_cost': labor_cost,
        'overhead_cost': overhead_cost,
        'packaging_cost': packaging_cost,
        'total_cost': total_cost,
        'recommended_price': recommended_price,
        'cost_per_unit': total_cost / batch_size,
        'price_per_unit': recommended_price / batch_size,
        'material_details': material_details
    }


@app.route('/cost-analysis')
def cost_analysis():
    products = Product.query.all()
    return render_template('cost_analysis.html', products=products)


@app.route('/api/calculate-cost', methods=['POST'])
def api_calculate_cost():
    data = request.json
    product_id = data.get('product_id')
    batch_size = data.get('batch_size')

    try:
        cost_data = calculate_product_cost(product_id, batch_size)
        stock_data = check_stock_availability(product_id, batch_size)

        # Save analysis
        analysis = CostAnalysis(
            product_id=product_id,
            batch_size=batch_size,
            material_cost=cost_data['material_cost'],
            labor_cost=cost_data['labor_cost'],
            overhead_cost=cost_data['overhead_cost'],
            packaging_cost=cost_data['packaging_cost'],
            total_cost=cost_data['total_cost'],
            recommended_price=cost_data['recommended_price']
        )
        db.session.add(analysis)
        db.session.commit()

        return jsonify({
            'success': True,
            'cost_data': {
                'material_cost': cost_data['material_cost'],
                'labor_cost': cost_data['labor_cost'],
                'overhead_cost': cost_data['overhead_cost'],
                'packaging_cost': cost_data['packaging_cost'],
                'total_cost': cost_data['total_cost'],
                'recommended_price': cost_data['recommended_price'],
                'cost_per_unit': cost_data['cost_per_unit'],
                'price_per_unit': cost_data['price_per_unit'],
                'material_details': cost_data['material_details']
            },
            'stock_data': stock_data
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/market-intelligence')
def market_intelligence():
    market_data = MarketPrice.query.order_by(MarketPrice.scraped_at.desc()).all()
    return render_template('market_intelligence.html', market_data=market_data)


@app.route('/api/scrape-prices', methods=['POST'])
def api_scrape_prices():
    data = request.json
    search_term = data.get('search_term', '')

    if not search_term:
        return jsonify({'success': False, 'error': 'Search term is required'})

    try:
        scraper = MarketScraper()
        results = scraper.scrape_jumia_prices(search_term)

        # Save to database
        for result in results:
            market_price = MarketPrice(
                product_name=result['name'],
                competitor=result['competitor'],
                price=result['price'],
                url=result['url'],
                size_info=result['size_info']
            )
            db.session.add(market_price)

        db.session.commit()

        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/price-comparison')
def price_comparison():
    products = Product.query.all()
    return render_template('price_comparison.html', products=products)


@app.route('/api/price-comparison/<int:product_id>')
def api_price_comparison(product_id):
    try:
        cost_data = calculate_product_cost(product_id)

        # Get recent market data for similar products
        product = Product.query.get_or_404(product_id)
        market_prices = MarketPrice.query.filter(
            MarketPrice.product_name.contains(product.name.split()[0])
        ).order_by(MarketPrice.scraped_at.desc()).limit(10).all()

        market_data = []
        for mp in market_prices:
            market_data.append({
                'name': mp.product_name,
                'price': mp.price,
                'competitor': mp.competitor,
                'size_info': mp.size_info,
                'scraped_at': mp.scraped_at.strftime('%Y-%m-%d %H:%M')
            })

        return jsonify({
            'success': True,
            'product_cost': {
                'name': product.name,
                'total_cost': cost_data['total_cost'],
                'recommended_price': cost_data['recommended_price'],
                'cost_per_unit': cost_data['cost_per_unit'],
                'price_per_unit': cost_data['price_per_unit']
            },
            'market_data': market_data
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# Initialize database
def create_tables():
    with app.app_context():
        db.create_all()


if __name__ == '__main__':
    # Create tables before running the app
    create_tables()
    app.run(debug=True)