"""Enhanced prompts for ResolveAI customer support agent.

This module contains optimized prompts for:
- Intent classification
- Policy question answering
- Order status responses
- Refund processing
- Address change handling
"""


def build_intent_classification_prompt(message: str) -> str:
    """Build prompt for intent classification with enhanced examples.
    
    Uses few-shot prompting with examples for better accuracy.
    """
    return f"""You are a customer support intent classifier. Analyze the customer message and classify it into exactly one of these intents:

INTENTS:
1. order_status - Customer asking about order location, tracking, delivery status, or when order will arrive
2. refund - Customer requesting a refund, return, or money back
3. address_change - Customer wanting to change, update, or modify shipping/delivery address
4. policy_question - Customer asking about policies, rules, or general information (shipping policy, return policy, warranty, payment methods, etc.)

EXAMPLES:
- "Where is my order?" → order_status
- "Track my package ORD-123456" → order_status
- "When will my order arrive?" → order_status
- "I want a refund" → refund
- "Can I return this item?" → refund
- "The item is damaged, I want my money back" → refund
- "Change my address to 123 Main St" → address_change
- "Update shipping address for my order" → address_change
- "What is your return policy?" → policy_question
- "How long does shipping take?" → policy_question
- "Do you offer warranty?" → policy_question
- "Đơn hàng của tôi đang ở đâu?" → order_status (Vietnamese)
- "Tôi muốn hoàn tiền" → refund (Vietnamese)
- "Đổi địa chỉ giao hàng" → address_change (Vietnamese)

IMPORTANT RULES:
- If the message contains both a refund request AND a policy question, classify as "refund"
- If the message asks about an order AND mentions address change, classify as "address_change"
- Default to "policy_question" only if no other intent clearly matches
- Respond with ONLY the intent name, nothing else

Message: {message}

Intent:"""


def build_policy_prompt(question: str, policy_context: str, language: str) -> str:
    """Build prompt for policy questions with comprehensive guidance.
    
    Provides structured format for accurate and helpful responses.
    """
    language_name = "Vietnamese" if language == "vi" else "English"
    language_instruction = (
        "Respond in Vietnamese using formal tone (bạn, quý khách)."
        if language == "vi"
        else "Respond in English using professional but friendly tone."
    )
    
    return f"""You are a knowledgeable customer support agent for ResolveAI. Your role is to provide accurate, helpful information about company policies.

INSTRUCTIONS:
1. Answer the question using ONLY the information from the Policy Context below
2. {language_instruction}
3. If the answer is not in the context, say so honestly and suggest contacting support
4. Be specific and include relevant details (timeframes, requirements, fees, etc.)
5. Format your response clearly with bullet points when appropriate
6. Include relevant next steps or call-to-action when applicable

RESPONSE FORMAT:
- Start with a direct answer to the question
- Provide supporting details
- End with any actions the customer should take

Question:
{question}

Policy Context:
{policy_context}

Your Response:"""


def build_order_status_prompt(order_id: str, status: str, tracking_number: str, language: str) -> str:
    """Build prompt for order status responses."""
    language_name = "Vietnamese" if language == "vi" else "English"
    
    status_messages = {
        "en": {
            "pending": f"Your order {order_id} is currently pending and will be processed soon. We'll send you a confirmation email once it ships.",
            "processing": f"Your order {order_id} is being processed. Our team is preparing your items for shipment.",
            "shipped": f"Great news! Your order {order_id} has been shipped. Tracking number: {tracking_number}. You can track your package using this number.",
            "out_for_delivery": f"Your order {order_id} is out for delivery today! You should receive it by end of day.",
            "delivered": f"Your order {order_id} was successfully delivered. We hope you enjoy your purchase!",
        },
        "vi": {
            "pending": f"Đơn hàng {order_id} của bạn đang chờ xử lý. Chúng tôi sẽ gửi email xác nhận khi đơn hàng được gửi.",
            "processing": f"Đơn hàng {order_id} đang được xử lý. Đội ngũ của chúng tôi đang chuẩn bị hàng để giao.",
            "shipped": f"Tin tốt! Đơn hàng {order_id} đã được gửi. Mã vận đơn: {tracking_number}. Bạn có thể theo dõi đơn hàng bằng mã này.",
            "out_for_delivery": f"Đơn hàng {order_id} đang được giao hôm nay! Bạn sẽ nhận được trước cuối ngày.",
            "delivered": f"Đơn hàng {order_id} đã được giao thành công. Hy vọng bạn hài lòng với sản phẩm!",
        }
    }
    
    return status_messages.get(language, status_messages["en"]).get(status, f"Your order {order_id} is currently: {status}")


def build_refund_response_prompt(
    order_id: str,
    decision: str,
    amount: float,
    reason: str | None,
    requires_evidence: bool,
    language: str
) -> str:
    """Build prompt for refund decision responses."""
    language_name = "Vietnamese" if language == "vi" else "English"
    
    if language == "vi":
        if decision == "approved":
            return f"✅ Yêu cầu hoàn tiền cho đơn hàng {order_id} đã được phê duyệt. Số tiền ${amount:.2f} sẽ được hoàn lại trong 5-10 ngày làm việc."
        elif decision == "requires_human":
            msg = f"⏳ Yêu cầu hoàn tiền cho đơn hàng {order_id} đang được nhân viên xem xét."
            if requires_evidence:
                msg += " Vui lòng gửi ảnh bằng chứng (ảnh sản phẩm bị hỏng/sai) để hỗ trợ yêu cầu của bạn."
            return msg
        else:
            return f"❌ Rất tiếc, đơn hàng {order_id} không đủ điều kiện hoàn tiền theo chính sách hiện tại."
    else:
        if decision == "approved":
            return f"✅ Your refund for order {order_id} has been approved. ${amount:.2f} will be returned within 5-10 business days."
        elif decision == "requires_human":
            msg = f"⏳ Your refund request for order {order_id} is being reviewed by our team."
            if requires_evidence:
                msg += " Please provide photo evidence (damaged/wrong item) to support your request."
            return msg
        else:
            return f"❌ Unfortunately, order {order_id} is not eligible for a refund under our current policy."


def build_address_change_response(
    order_id: str,
    success: bool,
    new_address: str,
    reason: str | None,
    language: str
) -> str:
    """Build response for address change requests."""
    if language == "vi":
        if success:
            return f"✅ Địa chỉ giao hàng cho đơn hàng {order_id} đã được cập nhật thành công đến: {new_address}"
        else:
            reasons = {
                "already_shipped": "Đơn hàng đã được gửi, không thể thay đổi địa chỉ.",
                "not_allowed": "Đơn hàng này không cho phép thay đổi địa chỉ (có thể do giới hạn chính sách hoặc rủi ro bảo mật).",
                "high_risk": "Đơn hàng này có cờ rủi ro cao. Vui lòng liên hệ bộ phận hỗ trợ để được hỗ trợ.",
            }
            reason_msg = reasons.get(reason, "Không thể thay đổi địa chỉ cho đơn hàng này.")
            return f"❌ Không thể thay đổi địa chỉ cho đơn hàng {order_id}. {reason_msg}"
    else:
        if success:
            return f"✅ Shipping address for order {order_id} has been successfully updated to: {new_address}"
        else:
            reasons = {
                "already_shipped": "Order has already shipped, address cannot be changed.",
                "not_allowed": "This order does not allow address changes (may be due to policy restrictions or security flags).",
                "high_risk": "This order has a high-risk flag. Please contact support for assistance.",
            }
            reason_msg = reasons.get(reason, "Unable to change address for this order.")
            return f"❌ Cannot change address for order {order_id}. {reason_msg}"


def build_escalation_prompt(intent: str, reason: str, order_id: str | None) -> str:
    """Build prompt for escalation responses."""
    return f"""Your request requires human review because: {reason}

Our team has been notified and will contact you within 24 hours. 
{'Please have your order number ready: ' + order_id if order_id else ''}

You can also:
- Call us at 1-800-RESOLVE (24/7)
- Email support@resolveai.com
- Use live chat on our website

Thank you for your patience. We're here to help!"""
