//订单管理页面 JS
document.addEventListener('DOMContentLoaded', function() {
    // 1. 订单筛选（按用户名/时间/状态）
    const filterForm = document.querySelector('#order-filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const username = document.querySelector('#username').value.trim();
            const startDate = document.querySelector('#start-date').value;
            const endDate = document.querySelector('#end-date').value;
            const status = document.querySelector('#order-status').value;

            // 构建查询参数
            const params = new URLSearchParams();
            if (username) params.append('username', username);
            if (startDate) params.append('start_date', startDate);
            if (endDate) params.append('end_date', endDate);
            if (status) params.append('status', status);

            // 跳转筛选
            window.location.href = `/admin/order_manage?${params.toString()}`;
        });
    }

    // 2. 修改订单状态
    const statusBtns = document.querySelectorAll('.update-status');
    statusBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const orderId = this.dataset.orderId;
            const currentStatus = this.dataset.currentStatus;
            const newStatus = currentStatus === '已支付' ? '已发货' : '已完成'; // 状态流转示例

            if (confirm(`确定要将订单 ${orderId} 状态修改为【${newStatus}】吗？`)) {
                fetch('/admin/api/order/update_status', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        order_id: orderId,
                        status: newStatus
                    })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        adminToast('订单状态修改成功');
                        // 更新页面状态显示
                        const statusElem = this.closest('tr').querySelector('.order-status');
                        statusElem.textContent = newStatus;
                        // 更新按钮状态
                        this.dataset.currentStatus = newStatus;
                        this.textContent = newStatus === '已发货' ? '标记为已完成' : '已完成';
                        if (newStatus === '已完成') this.disabled = true;
                    } else {
                        adminToast('修改失败：' + data.msg, false);
                    }
                });
            }
        });
    });

    // 3. 查看订单详情（弹窗显示）
    const detailBtns = document.querySelectorAll('.view-detail');
    const detailModal = document.querySelector('#order-detail-modal');
    const closeModal = document.querySelector('.close-modal');
    if (detailBtns && detailModal && closeModal) {
        detailBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const orderId = this.dataset.orderId;

                // 从后端获取订单详情
                fetch(`/admin/api/order/detail?order_id=${orderId}`)
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            const order = data.order;
                            // 填充详情数据到弹窗
                            document.querySelector('#modal-order-id').textContent = order.order_id;
                            document.querySelector('#modal-username').textContent = order.username;
                            document.querySelector('#modal-total').textContent = order.total_amount.toFixed(2);
                            document.querySelector('#modal-status').textContent = order.status;
                            document.querySelector('#modal-time').textContent = order.create_time;

                            // 填充订单项
                            const itemsList = document.querySelector('#modal-items');
                            itemsList.innerHTML = '';
                            order.items.forEach(item => {
                                const li = document.createElement('li');
                                li.style.padding = '8px 0';
                                li.style.borderBottom = '1px solid #f0f0f0';
                                li.innerHTML = `
                                    商品：${item.name} | 数量：${item.quantity} | 
                                    单价：¥${item.price.toFixed(2)} | 小计：¥${(item.price * item.quantity).toFixed(2)}
                                `;
                                itemsList.appendChild(li);
                            });

                            // 显示弹窗
                            detailModal.style.display = 'block';
                        } else {
                            adminToast('获取详情失败：' + data.msg, false);
                        }
                    });
            });
        });

        // 关闭弹窗
        closeModal.addEventListener('click', function() {
            detailModal.style.display = 'none';
        });

        // 点击弹窗外部关闭
        window.addEventListener('click', function(e) {
            if (e.target === detailModal) detailModal.style.display = 'none';
        });
    }
});