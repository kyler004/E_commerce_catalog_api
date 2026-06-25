import random
from django.core.management.base import BaseCommand
from api.models import Category, Product, Variant, Inventory

class Command(BaseCommand):
    help = 'Populates the database with realistic shoe products, variants, and inventory.'

    def handle(self, *args, **options):
        self.stdout.write('Populating database with shoe products...')

        # 1. Create Shoes Category
        shoes_cat, created = Category.objects.get_or_create(
            name='Shoes',
            defaults={'description': 'Footwear for all occasions and activities.'}
        )

        subcategories_data = [
            ('Running Shoes', 'High-performance running and athletic shoes.'),
            ('Sneakers', 'Casual sneakers for daily wear and street style.'),
            ('Boots', 'Durable and rugged boots for outdoors and fashion.'),
            ('Formal Shoes', 'Elegant shoes for formal events and office wear.')
        ]

        subcategories = {}
        for name, desc in subcategories_data:
            sub_cat, created = Category.objects.get_or_create(
                name=name,
                defaults={'description': desc, 'parent': shoes_cat}
            )
            subcategories[name] = sub_cat

        # 2. Products Data
        shoes_data = [
            {
                'name': 'Nike Air Zoom Pegasus 40',
                'description': 'A springy ride for every run, the Peg’s familiar, just-for-you feel returns to help you accomplish your goals. This version has the same responsiveness and neutral support you love, but with improved comfort in those sensitive areas of your foot, like the arch and toes.',
                'price': 130.00,
                'category': subcategories['Running Shoes'],
                'image_url': 'https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?q=80&w=1000&auto=format&fit=crop',
                'variants': [
                    {'size': '8', 'colors': ['Black', 'White', 'Blue']},
                    {'size': '9', 'colors': ['Black', 'White', 'Blue']},
                    {'size': '10', 'colors': ['Black', 'White', 'Red']},
                    {'size': '11', 'colors': ['Black', 'White', 'Red']},
                ]
            },
            {
                'name': 'Adidas Ultraboost Light',
                'description': 'Experience epic energy with the new Adidas Ultraboost Light, our lightest Ultraboost ever. The magic lies in the Light BOOST midsole, a new generation of Adidas BOOST that provides even more energy return and cushioning.',
                'price': 190.00,
                'category': subcategories['Running Shoes'],
                'image_url': 'https://images.unsplash.com/photo-1587563876166-16347b23c152?q=80&w=1000&auto=format&fit=crop',
                'variants': [
                    {'size': '8', 'colors': ['Grey', 'Black', 'White']},
                    {'size': '9', 'colors': ['Grey', 'Black', 'White']},
                    {'size': '10', 'colors': ['Grey', 'Black', 'White']},
                    {'size': '11', 'colors': ['Black', 'White']},
                ]
            },
            {
                'name': 'Puma Suede Classic',
                'description': 'The Suede Classic has been kicking it since 1968. From 1980s b-boys to modern street culture lovers, it has been worn by generations of style icons. Featuring a full suede upper and clean retro look.',
                'price': 75.00,
                'category': subcategories['Sneakers'],
                'image_url': 'https://images.unsplash.com/photo-1608231387042-66d1773070a5?q=80&w=1000&auto=format&fit=crop',
                'variants': [
                    {'size': '7', 'colors': ['Black', 'Red']},
                    {'size': '8', 'colors': ['Black', 'Red', 'Blue']},
                    {'size': '9', 'colors': ['Black', 'Red', 'Blue']},
                    {'size': '10', 'colors': ['Black', 'Red']},
                    {'size': '11', 'colors': ['Black']},
                ]
            },
            {
                'name': 'Converse Chuck Taylor All Star',
                'description': 'The original basketball shoe, now a cultural icon. Created in 1917, the Chuck Taylor All Star has defined casual style for over a century. Features classic canvas upper and signature ankle patch.',
                'price': 65.00,
                'category': subcategories['Sneakers'],
                'image_url': 'https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?q=80&w=1000&auto=format&fit=crop',
                'variants': [
                    {'size': '8', 'colors': ['White', 'Black']},
                    {'size': '9', 'colors': ['White', 'Black']},
                    {'size': '10', 'colors': ['White', 'Black']},
                    {'size': '11', 'colors': ['White', 'Black']},
                ]
            },
            {
                'name': 'Timberland Premium 6-Inch Waterproof Boot',
                'description': 'Crafted in premium waterproof leather with sealed seams to keep feet dry, these rugged work boots are as functional as they are fashionable. Features PrimaLoft insulation and fatigue-reducing footbeds.',
                'price': 198.00,
                'category': subcategories['Boots'],
                'image_url': 'https://images.unsplash.com/photo-1520639888713-7851133b1ed0?q=80&w=1000&auto=format&fit=crop',
                'variants': [
                    {'size': '8', 'colors': ['Wheat', 'Black']},
                    {'size': '9', 'colors': ['Wheat', 'Black']},
                    {'size': '10', 'colors': ['Wheat', 'Black']},
                    {'size': '11', 'colors': ['Wheat']},
                ]
            },
            {
                'name': 'Vans Old Skool',
                'description': 'First known as the Vans #36, the Old Skool debuted in 1977 with a unique new addition: a random doodle drawn by founder Paul Van Doren, and originally referred to as the "jazz stripe." Today, the famous Vans Sidestripe has become the unmistakable hallmark of the brand.',
                'price': 70.00,
                'category': subcategories['Sneakers'],
                'image_url': 'https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?q=80&w=1000&auto=format&fit=crop',
                'variants': [
                    {'size': '8', 'colors': ['Black/White', 'Navy']},
                    {'size': '9', 'colors': ['Black/White', 'Navy']},
                    {'size': '10', 'colors': ['Black/White', 'Navy']},
                    {'size': '11', 'colors': ['Black/White']},
                ]
            },
            {
                'name': 'Oxford Leather Dress Shoes',
                'description': 'Classic formal oxford shoes crafted from genuine premium leather. Perfect for weddings, business meetings, and formal events. Features comfortable cushioned insole and durable rubber outsole.',
                'price': 110.00,
                'category': subcategories['Formal Shoes'],
                'image_url': 'https://images.unsplash.com/photo-1549298916-b41d501d3772?q=80&w=1000&auto=format&fit=crop',
                'variants': [
                    {'size': '8', 'colors': ['Brown', 'Black']},
                    {'size': '9', 'colors': ['Brown', 'Black']},
                    {'size': '10', 'colors': ['Brown', 'Black']},
                    {'size': '11', 'colors': ['Brown', 'Black']},
                ]
            }
        ]

        # 3. Create Products, Variants and Inventories
        for p_data in shoes_data:
            product, created = Product.objects.get_or_create(
                name=p_data['name'],
                defaults={
                    'description': p_data['description'],
                    'price': p_data['price'],
                    'category': p_data['category'],
                    'image_url': p_data['image_url']
                }
            )
            if created:
                self.stdout.write(f"Created product: {product.name}")
            else:
                product.description = p_data['description']
                product.price = p_data['price']
                product.category = p_data['category']
                product.image_url = p_data['image_url']
                product.save()
                self.stdout.write(f"Updated product: {product.name}")

            # Create variants & inventory
            for var_spec in p_data['variants']:
                size = var_spec['size']
                for color in var_spec['colors']:
                    sku = f"{product.id}-{size}-{color.replace('/', '').replace(' ', '').upper()}"
                    
                    variant, var_created = Variant.objects.get_or_create(
                        product=product,
                        size=size,
                        color=color,
                        defaults={'sku': sku}
                    )
                    
                    quantity = random.randint(15, 60)
                    inventory, inv_created = Inventory.objects.get_or_create(
                        variant=variant,
                        defaults={'quantity': quantity}
                    )
                    if not inv_created:
                        inventory.quantity = quantity
                        inventory.save()

        self.stdout.write(self.style.SUCCESS('Successfully populated database with shoe products!'))
