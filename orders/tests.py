# class StripeCheckoutSessionView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request, *args, **kwargs):
#         order_id = request.data.get("order_id")
#         try:
#             order = Order.objects.get(id=order_id, user=request.user)
#         except Order.DoesNotExist:
#             return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

#         if order.payment_status == "PAID":
#             return Response({"message": "Order already paid."}, status=status.HTTP_400_BAD_REQUEST)

#         # Create Stripe checkout session
#         session = stripe.checkout.Session.create(
#             payment_method_types=["card"],
#             line_items=[
#                 {
#                     "price_data": {
#                         "currency": "usd",
#                         "product_data": {
#                             "name": f"Order #{order.id}"
#                         },
#                         "unit_amount": int(order.total_price * 100),  # Convert to cents
#                     },
#                     "quantity": 1,
#                 }
#             ],
#             mode="payment",
#             success_url=settings.FRONTEND_URL + "/orders/success?session_id={CHECKOUT_SESSION_ID}",
#             cancel_url=settings.FRONTEND_URL + f"/orders/{order.id}",
#             metadata={"order_id": order.id}
#         )

#         return Response({"session_id": session.id, "url": session.url}, status=status.HTTP_200_OK)

