//结算页面 JS
document.addEventListener('DOMContentLoaded', function() {
    const checkoutForm = document.querySelector('.checkout-form');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function(e) {
            e.preventDefault(); // 阻止默认表单提交

            // 1. 表单验证
            const recipient = document.querySelector('#recipient').value.trim();
            const phone = document.querySelector('#phone').value.trim();
            const address = document.querySelector('#address').value.trim();

            if (!recipient) {
                showToast('请填写收货人姓名', false);
                return;
            }

            // 手机号格式验证
            const phoneReg = /^1[3-9]\d{9}$/;
            if (!phoneReg.test(phone)) {
                showToast('请填写正确的手机号', false);
                return;
            }

            if (!address) {
                showToast('请填写收货地址', false);
                return;
            }

            // 2. 提交订单到后端
            fetch('/api/purchase', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    recipient: recipient,
                    phone: phone,
                    address: address
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast('下单成功！即将跳转到我的订单');
                    setTimeout(() => window.location.href = '/profile/orders', 2000);
                } else {
                    showToast('下单失败：' + data.msg, false);
                }
            })
            .catch(err => {
                console.error('下单失败：', err);
                showToast('网络错误，下单失败', false);
            });
        });
    }
});