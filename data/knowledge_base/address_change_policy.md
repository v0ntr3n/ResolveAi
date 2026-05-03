# Address Change Policy

## English

- Shipping addresses can be updated only while an order is in `pending` or `processing` status.
- Orders in `shipped`, `out_for_delivery`, or `delivered` status cannot be changed automatically.
- Customers must provide the full replacement address in one message for automatic processing.
- If the address appears incomplete, the request is escalated instead of being applied.
- Orders marked with `address_change_allowed = false` are blocked from automatic updates.
- High-risk orders should be reviewed by a human even if the order is still in a pre-shipment state.

## Vietnamese

- Địa chỉ giao hàng chỉ có thể được cập nhật khi đơn hàng đang ở trạng thái `pending` hoặc `processing`.
- Các đơn hàng ở trạng thái `shipped`, `out_for_delivery`, hoặc `delivered` sẽ không được đổi địa chỉ tự động.
- Khách hàng phải cung cấp đầy đủ địa chỉ mới trong một tin nhắn để hệ thống xử lý tự động.
- Nếu địa chỉ có vẻ chưa đầy đủ, yêu cầu sẽ được chuyển cho nhân viên thay vì cập nhật ngay.
- Các đơn hàng có `address_change_allowed = false` sẽ bị chặn cập nhật tự động.
- Các đơn hàng có rủi ro cao nên được nhân viên xem xét ngay cả khi vẫn đang ở giai đoạn trước khi giao.
