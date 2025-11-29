//商品页 / 首页交互 JS
document.addEventListener('DOMContentLoaded', function() {
    // 1. 加入购物车功能（商品卡片/商品详情页通用）
    const addToCartBtns = document.querySelectorAll('.add-to-cart');
    addToCartBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // 获取商品信息（从 HTML 标签的 data 属性中获取，需要在模板中添加 data-* 属性）
            const productCard = this.closest('.product-card') || this.closest('.product-detail');
            const productId = productCard.dataset.productId;
            const productName = productCard.dataset.productName;
            const quantity = parseInt(document.querySelector('.quantity-input')?.value || 1); // 详情页可输入数量

            // 检查登录状态
            if (!sessionStorage.getItem('username')) {
                showToast('请先登录再加入购物车', false);
                setTimeout(() => window.location.href = '/login', 1500);
                return;
            }

            // 发送 AJAX 请求到后端购物车接口
            fetch('/api/cart/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    product_id: productId,
                    quantity: quantity
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast(`商品《${productName}》已加入购物车`);
                    // 更新导航栏购物车数量
                    updateCartCount();
                } else {
                    showToast('加入失败：' + data.msg, false);
                }
            })
            .catch(err => {
                console.error('加入购物车失败：', err);
                showToast('网络错误，加入购物车失败', false);
            });
        });
    });

    // 2. 商品详情页：数量调整（+/- 按钮）
    const minusBtn = document.querySelector('.quantity-minus');
    const plusBtn = document.querySelector('.quantity-plus');
    const quantityInput = document.querySelector('.quantity-input');
    if (minusBtn && plusBtn && quantityInput) {
        minusBtn.addEventListener('click', function() {
            let current = parseInt(quantityInput.value);
            if (current > 1) quantityInput.value = current - 1;
        });

        plusBtn.addEventListener('click', function() {
            let current = parseInt(quantityInput.value);
            quantityInput.value = current + 1;
        });

        // 限制输入为正整数
        quantityInput.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value === '' || parseInt(this.value) < 1) this.value = 1;
        });
    }

    // 3. 更新导航栏购物车数量（需要后端提供获取购物车数量的接口）
    function updateCartCount() {
        fetch('/api/cart/count')
            .then(res => res.json())
            .then(data => {
                const cartCount = document.querySelector('.cart-icon .count');
                if (cartCount) cartCount.textContent = data.count || 0;
            });
    }

    // 初始化：加载购物车数量
    updateCartCount();
});