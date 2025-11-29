//购物车页面 JS
document.addEventListener('DOMContentLoaded', function() {
    // 1. 数量调整（+/- 按钮）
    const quantityControls = document.querySelectorAll('.quantity-control');
    quantityControls.forEach(control => {
        const minusBtn = control.querySelector('.minus');
        const plusBtn = control.querySelector('.plus');
        const input = control.querySelector('input');
        const productId = control.closest('tr').dataset.productId;

        minusBtn.addEventListener('click', function() {
            let current = parseInt(input.value);
            if (current > 1) {
                input.value = current - 1;
                updateCartItem(productId, input.value); // 同步到后端
            }
        });

        plusBtn.addEventListener('click', function() {
            let current = parseInt(input.value);
            input.value = current + 1;
            updateCartItem(productId, input.value); // 同步到后端
        });

        // 输入框变化时同步
        input.addEventListener('change', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value === '' || parseInt(this.value) < 1) this.value = 1;
            updateCartItem(productId, this.value);
        });
    });

    // 2. 删除购物车商品
    const deleteBtns = document.querySelectorAll('.cart-delete');
    deleteBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tr = this.closest('tr');
            const productId = tr.dataset.productId;
            const productName = tr.querySelector('.cart-product-name').textContent;

            if (confirm(`确定要删除商品《${productName}》吗？`)) {
                fetch('/api/cart/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ product_id: productId })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        showToast('删除成功');
                        tr.remove(); // 从页面移除
                        updateTotalAmount(); // 更新总金额
                        updateCartCount(); // 更新导航栏数量
                    } else {
                        showToast('删除失败：' + data.msg, false);
                    }
                });
            }
        });
    });

    // 3. 结算功能
    const checkoutBtn = document.querySelector('.checkout-btn');
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', function() {
            // 检查购物车是否为空
            const cartItems = document.querySelectorAll('.cart-table tbody tr');
            if (cartItems.length === 0) {
                showToast('购物车为空，无法结算', false);
                return;
            }

            // 跳转到结算页面（需要后端提供 checkout.html 模板）
            window.location.href = '/checkout';
        });
    }

    // 4. 同步购物车商品数量到后端
    function updateCartItem(productId, quantity) {
        fetch('/api/cart/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_id: productId,
                quantity: parseInt(quantity)
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                updateTotalAmount(); // 更新总金额
            } else {
                showToast('更新失败：' + data.msg, false);
                // 回滚输入框值
                input.value = data.oldQuantity || 1;
            }
        });
    }

    // 5. 更新购物车总金额（需要后端返回，或前端计算）
    function updateTotalAmount() {
        fetch('/api/cart/total')
            .then(res => res.json())
            .then(data => {
                const totalElem = document.querySelector('.total-amount span');
                if (totalElem) totalElem.textContent = data.total.toFixed(2);
            });
    }

    // 6. 更新导航栏购物车数量（复用 base.js 的函数）
    function updateCartCount() {
        fetch('/api/cart/count')
            .then(res => res.json())
            .then(data => {
                const cartCount = document.querySelector('.cart-icon .count');
                if (cartCount) cartCount.textContent = data.count || 0;
            });
    }

    // 初始化：加载总金额
    updateTotalAmount();
});