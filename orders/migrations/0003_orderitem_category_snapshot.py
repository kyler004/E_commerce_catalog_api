from django.db import migrations, models


def backfill_order_item_categories(apps, schema_editor):
    OrderItem = apps.get_model('orders', 'OrderItem')
    items_to_update = []
    order_items = OrderItem.objects.select_related('variant__product__category')

    for item in order_items:
        if item.variant_id is None:
            continue
        category = item.variant.product.category
        item.category_id = category.id
        item.category_name = category.name
        items_to_update.append(item)

    if items_to_update:
        OrderItem.objects.bulk_update(
            items_to_update,
            ['category_id', 'category_name'],
        )


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_order_discount_amount_order_promotion_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='category_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='category_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.RunPython(
            backfill_order_item_categories,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
