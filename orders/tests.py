
# class OrderViewSet(viewsets.ViewSet):
#     permission_classes = [IsAuthenticated]
#     serializer_class = OrderSerializer  

#     def create(self, request):
#         """Place an order from selected cart items."""
#         user = request.user
#         cart = Cart.objects.filter(user=user).first()

#         if not cart or not cart.items.exists():
#             return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

#         selected_item_ids = request.data.get("cart_item_ids", [])  # List of selected cart item IDs
#         if not selected_item_ids:
#             return Response({"error": "No items selected"}, status=status.HTTP_400_BAD_REQUEST)
#         payment_method = request.data.get("payment_method", "cod").lower() # Default to COD

#         orders = []  # To store created orders
#         store_orders = {}  # Group selected cart items by store

#         # Filter only selected items
#         selected_items = cart.items.filter(id__in=selected_item_ids)
        
#         if not selected_items.exists():
#             return Response({"error": "No valid items found"}, status=status.HTTP_400_BAD_REQUEST)

#         # Group selected items by store
#         for item in selected_items:
#             store_orders.setdefault(item.book.store, []).append(item)

#         with transaction.atomic():  # Ensure atomicity
#             for store, items in store_orders.items():
#                 total_price = sum(item.total_price for item in items)
#                 order = Order.objects.create(
#                     user=user,
#                     store=store,
#                     total_price=total_price,
#                     payment_method=payment_method,
#                     payment_status = "pending"
#                 )
#                 for item in items:
#                     OrderItem.objects.create(
#                         order=order,
#                         book=item.book,
#                         quantity=item.quantity,
#                         price=item.price
#                     )

#                 # **Create a Transaction for this order**
#                 admin_fee = total_price * Decimal("0.10")  # 10% fee
#                 store_earnings = total_price - admin_fee

#                 Transaction.objects.create(
#                     order=order,
#                     store=store,
#                     amount=total_price,
#                     admin_fee=admin_fee,
#                     store_earnings=store_earnings,
#                     payment_method=payment_method,
#                     payment_status="pending"  # Will update after payment
#                 )
#                 orders.append(order)
                

#             # Remove only the ordered items from the cart
#             selected_items.delete()

#         return Response(OrderSerializer(orders, many=True).data, status=status.HTTP_201_CREATED)

