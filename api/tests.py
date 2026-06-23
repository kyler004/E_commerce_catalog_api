from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from .models import Category, Inventory, Product, Variant


class CatalogFixturesMixin:
    """Shared catalog data for API tests."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='catalog@test.com',
            password='TestPass123!',
            is_active=True,
        )
        self.user.email_verified_at = timezone.now()
        self.user.save(update_fields=['email_verified_at'])
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(
            name="Electronics",
            description="Electronic devices",
        )
        self.subcategory = Category.objects.create(
            name="Headphones",
            description="Audio devices",
            parent=self.category,
        )
        self.product = Product.objects.create(
            name="Wireless Headphones",
            description="Noise-cancelling headphones",
            price=Decimal("79.99"),
            category=self.category,
        )
        self.variant = Variant.objects.create(
            product=self.product,
            size="L",
            color="Red",
            sku="WH-L-RED",
        )
        self.inventory = Inventory.objects.create(
            variant=self.variant,
            quantity=50,
        )


class CategoryAPITestCase(CatalogFixturesMixin, TestCase):
    url = "/api/categories/"

    def test_list_categories(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 2)

    def test_retrieve_category_with_nested_products(self):
        response = self.client.get(f"{self.url}{self.category.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["name"], "Electronics")
        self.assertEqual(len(data["products"]), 1)
        self.assertEqual(data["products"][0]["name"], "Wireless Headphones")
        self.assertEqual(len(data["products"][0]["variants"]), 1)
        self.assertEqual(data["products"][0]["variants"][0]["inventory"]["quantity"], 50)

    def test_create_category(self):
        response = self.client.post(
            self.url,
            {"name": "Clothing", "description": "Apparel", "parent": None},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.filter(name="Clothing").count(), 1)

    def test_update_category(self):
        response = self.client.put(
            f"{self.url}{self.category.id}/",
            {
                "name": "Electronics Updated",
                "description": "Updated description",
                "parent": None,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Electronics Updated")

    def test_partial_update_category(self):
        response = self.client.patch(
            f"{self.url}{self.category.id}/",
            {"description": "Partial update"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.description, "Partial update")

    def test_delete_category(self):
        category = Category.objects.create(name="Temporary")
        response = self.client.delete(f"{self.url}{category.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(id=category.id).exists())

    def test_retrieve_nonexistent_category_returns_404(self):
        response = self.client.get(f"{self.url}9999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_by_parent(self):
        response = self.client.get(self.url, {"parent": self.category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Headphones")

    def test_filter_by_name(self):
        response = self.client.get(self.url, {"name": "Electronics"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.category.id)

    def test_search_categories(self):
        response = self.client.get(self.url, {"search": "audio"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Headphones")

    def test_ordering_categories_by_name(self):
        response = self.client.get(self.url, {"ordering": "name"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in response.json()["results"]]
        self.assertEqual(names, sorted(names))


class ProductAPITestCase(CatalogFixturesMixin, TestCase):
    url = "/api/products/"

    def test_list_products(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 1)

    def test_retrieve_product_with_nested_variants(self):
        response = self.client.get(f"{self.url}{self.product.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["name"], "Wireless Headphones")
        self.assertEqual(len(data["variants"]), 1)
        self.assertEqual(data["variants"][0]["sku"], "WH-L-RED")
        self.assertEqual(data["variants"][0]["inventory"]["quantity"], 50)

    def test_create_product(self):
        response = self.client.post(
            self.url,
            {
                "name": "Smart Watch",
                "description": "Fitness tracker",
                "price": "199.99",
                "category": self.category.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.filter(name="Smart Watch").count(), 1)

    def test_create_product_missing_required_fields_returns_400(self):
        response = self.client.post(
            self.url,
            {"name": "Incomplete Product"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_product(self):
        response = self.client.put(
            f"{self.url}{self.product.id}/",
            {
                "name": "Updated Headphones",
                "description": "Updated description",
                "price": "89.99",
                "category": self.category.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Updated Headphones")
        self.assertEqual(self.product.price, Decimal("89.99"))

    def test_partial_update_product(self):
        response = self.client.patch(
            f"{self.url}{self.product.id}/",
            {"price": "99.99"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, Decimal("99.99"))

    def test_delete_product(self):
        product = Product.objects.create(
            name="Temporary Product",
            description="To be deleted",
            price=Decimal("10.00"),
            category=self.category,
        )
        response = self.client.delete(f"{self.url}{product.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(id=product.id).exists())

    def test_retrieve_nonexistent_product_returns_404(self):
        response = self.client.get(f"{self.url}9999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_search_products(self):
        response = self.client.get(self.url, {"search": "noise"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.product.id)

    def test_ordering_products_by_price(self):
        Product.objects.create(
            name="Cheap Earbuds",
            description="Budget option",
            price=Decimal("19.99"),
            category=self.category,
        )
        response = self.client.get(self.url, {"ordering": "price"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = [Decimal(item["price"]) for item in response.json()["results"]]
        self.assertEqual(prices, sorted(prices))

    def test_filter_by_category(self):
        other_category = Category.objects.create(name="Books")
        Product.objects.create(
            name="Python Guide",
            description="Programming book",
            price=Decimal("29.99"),
            category=other_category,
        )
        response = self.client.get(self.url, {"category": self.category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.product.id)


class ProductFilterTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Electronics")

        self.p1 = Product.objects.create(
            name="Expensive Product",
            description="High end",
            price=Decimal("100.00"),
            category=self.category,
        )
        Variant.objects.create(product=self.p1, size="L", color="Red", sku="P1-L-RED")

        self.p2 = Product.objects.create(
            name="Cheap Product",
            description="Low end",
            price=Decimal("20.00"),
            category=self.category,
        )
        Variant.objects.create(product=self.p2, size="S", color="Blue", sku="P2-S-BLUE")

        self.p3 = Product.objects.create(
            name="Mid Product",
            description="Mid range",
            price=Decimal("50.00"),
            category=self.category,
        )
        Variant.objects.create(product=self.p3, size="S", color="Red", sku="P3-S-RED")

    def test_filter_by_price_range(self):
        response = self.client.get("/api/products/", {"min_price": 30, "max_price": 150})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 2)
        ids = [p["id"] for p in results]
        self.assertIn(self.p1.id, ids)
        self.assertIn(self.p3.id, ids)

    def test_filter_by_color(self):
        response = self.client.get("/api/products/", {"color": "Red"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 2)
        ids = [p["id"] for p in results]
        self.assertIn(self.p1.id, ids)
        self.assertIn(self.p3.id, ids)

    def test_filter_by_size(self):
        response = self.client.get("/api/products/", {"size": "S"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 2)
        ids = [p["id"] for p in results]
        self.assertIn(self.p2.id, ids)
        self.assertIn(self.p3.id, ids)

    def test_combined_filters(self):
        response = self.client.get("/api/products/", {"max_price": 80, "color": "Red"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.p3.id)


class VariantAPITestCase(CatalogFixturesMixin, TestCase):
    url = "/api/variants/"

    def test_list_variants(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 1)

    def test_retrieve_variant_with_inventory(self):
        response = self.client.get(f"{self.url}{self.variant.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["sku"], "WH-L-RED")
        self.assertEqual(data["inventory"]["quantity"], 50)

    def test_retrieve_variant_without_inventory(self):
        variant = Variant.objects.create(
            product=self.product,
            size="M",
            color="Blue",
            sku="WH-M-BLUE",
        )
        response = self.client.get(f"{self.url}{variant.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.json()["inventory"])

    def test_create_variant(self):
        response = self.client.post(
            self.url,
            {
                "product": self.product.id,
                "size": "S",
                "color": "Black",
                "sku": "WH-S-BLK",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Variant.objects.filter(sku="WH-S-BLK").exists())

    def test_update_variant(self):
        response = self.client.put(
            f"{self.url}{self.variant.id}/",
            {
                "product": self.product.id,
                "size": "XL",
                "color": "Red",
                "sku": "WH-XL-RED",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.size, "XL")
        self.assertEqual(self.variant.sku, "WH-XL-RED")

    def test_partial_update_variant(self):
        response = self.client.patch(
            f"{self.url}{self.variant.id}/",
            {"color": "Crimson"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.color, "Crimson")

    def test_delete_variant(self):
        variant = Variant.objects.create(
            product=self.product,
            size="M",
            color="Green",
            sku="WH-M-GRN",
        )
        response = self.client.delete(f"{self.url}{variant.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Variant.objects.filter(id=variant.id).exists())

    def test_retrieve_nonexistent_variant_returns_404(self):
        response = self.client.get(f"{self.url}9999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_by_product(self):
        other_product = Product.objects.create(
            name="Speaker",
            description="Bluetooth speaker",
            price=Decimal("49.99"),
            category=self.category,
        )
        Variant.objects.create(
            product=other_product,
            size="One",
            color="Black",
            sku="SP-ONE-BLK",
        )
        response = self.client.get(self.url, {"product": self.product.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.variant.id)

    def test_filter_by_size_and_color(self):
        response = self.client.get(self.url, {"size": "L", "color": "Red"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.variant.id)

    def test_search_by_sku(self):
        response = self.client.get(self.url, {"search": "WH-L-RED"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["sku"], "WH-L-RED")

    def test_duplicate_sku_returns_400(self):
        response = self.client.post(
            self.url,
            {
                "product": self.product.id,
                "size": "M",
                "color": "Red",
                "sku": "WH-L-RED",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class InventoryAPITestCase(CatalogFixturesMixin, TestCase):
    url = "/api/inventories/"

    def test_list_inventories(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 1)

    def test_retrieve_inventory(self):
        response = self.client.get(f"{self.url}{self.inventory.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["quantity"], 50)
        self.assertIn("last_updated", data)

    def test_update_inventory_quantity(self):
        response = self.client.patch(
            f"{self.url}{self.inventory.id}/",
            {"quantity": 25},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 25)

    def test_delete_inventory(self):
        variant = Variant.objects.create(
            product=self.product,
            size="S",
            color="White",
            sku="WH-S-WHT",
        )
        inventory = Inventory.objects.create(variant=variant, quantity=10)
        response = self.client.delete(f"{self.url}{inventory.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Inventory.objects.filter(id=inventory.id).exists())

    def test_retrieve_nonexistent_inventory_returns_404(self):
        response = self.client.get(f"{self.url}9999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_by_variant(self):
        response = self.client.get(self.url, {"variant": self.variant.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["quantity"], 50)

    def test_filter_by_quantity(self):
        response = self.client.get(self.url, {"quantity": 50})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)


class PaginationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Test Category")

    def test_product_pagination(self):
        for index in range(15):
            Product.objects.create(
                name=f"Product {index}",
                description=f"Description {index}",
                price=Decimal("10.00"),
                category=self.category,
            )

        response = self.client.get("/api/products/", {"page_size": 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["count"], 15)
        self.assertEqual(len(data["results"]), 5)
        self.assertIsNotNone(data["next"])
        self.assertIsNone(data["previous"])

        response = self.client.get("/api/products/", {"page": 2, "page_size": 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data["results"]), 5)
        self.assertIsNotNone(data["previous"])
        self.assertIsNotNone(data["next"])

    def test_page_size_capped_at_max(self):
        for index in range(12):
            Product.objects.create(
                name=f"Item {index}",
                description="Desc",
                price=Decimal("5.00"),
                category=self.category,
            )

        response = self.client.get("/api/products/", {"page_size": 200})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.json()["results"]), 100)


class ModelTestCase(CatalogFixturesMixin, TestCase):
    def test_category_str(self):
        self.assertEqual(str(self.category), "Electronics")

    def test_product_str(self):
        self.assertEqual(str(self.product), "Wireless Headphones")

    def test_variant_str(self):
        self.assertEqual(str(self.variant), "Wireless Headphones - L/Red")

    def test_inventory_str(self):
        self.assertIn("Wireless Headphones", str(self.inventory))

    def test_deleting_product_cascades_to_variants_and_inventory(self):
        product_id = self.product.id
        variant_id = self.variant.id
        inventory_id = self.inventory.id

        self.product.delete()

        self.assertFalse(Product.objects.filter(id=product_id).exists())
        self.assertFalse(Variant.objects.filter(id=variant_id).exists())
        self.assertFalse(Inventory.objects.filter(id=inventory_id).exists())

    def test_unique_sku_constraint(self):
        with self.assertRaises(IntegrityError):
            Variant.objects.create(
                product=self.product,
                size="M",
                color="Red",
                sku="WH-L-RED",
            )


class CatalogWriteAuthTestCase(CatalogFixturesMixin, TestCase):
    def test_unauthenticated_create_product_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            "/api/products/",
            {
                "name": "Blocked Product",
                "description": "Should fail",
                "price": "10.00",
                "category": self.category.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unverified_user_create_product_returns_403(self):
        unverified = User.objects.create_user(
            email='unverified@test.com',
            password='TestPass123!',
            is_active=False,
        )
        self.client.force_authenticate(user=unverified)
        response = self.client.post(
            "/api/products/",
            {
                "name": "Blocked Product",
                "description": "Should fail",
                "price": "10.00",
                "category": self.category.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_list_products_still_allowed(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
