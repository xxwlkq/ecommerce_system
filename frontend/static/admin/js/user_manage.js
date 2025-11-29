document.addEventListener('DOMContentLoaded', function() {
    // 1. 用户搜索（按用户名/用户ID）
    const searchForm = document.querySelector('#user-search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const keyword = document.querySelector('#search-keyword').value.trim();
            if (keyword) {
                window.location.href = `/admin/user_manage?keyword=${keyword}`;
            } else {
                adminToast('请输入搜索关键词', false);
            }
        });
    }

    // 2. 禁用/启用用户
    const toggleStatusBtns = document.querySelectorAll('.toggle-user-status');
    toggleStatusBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const userId = this.dataset.userId;
            const username = this.dataset.username;
            const currentStatus = this.dataset.status; // 0-禁用，1-正常
            const newStatus = currentStatus === '1' ? '0' : '1';
            const statusText = newStatus === '1' ? '正常' : '禁用';

            if (confirm(`确定要将用户 ${username} 状态修改为【${statusText}】吗？`)) {
                fetch('/admin/api/user/toggle_status', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: userId,
                        status: newStatus
                    })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        adminToast(`用户状态已修改为${statusText}`);
                        // 更新按钮显示
                        this.dataset.status = newStatus;
                        this.textContent = statusText === '正常' ? '禁用用户' : '启用用户';
                        this.style.backgroundColor = newStatus === '1' ? '#ef4444' : '#3b82f6';
                    } else {
                        adminToast('修改失败：' + data.msg, false);
                    }
                });
            }
        });
    });

    // 3. 调整用户余额
    const balanceBtns = document.querySelectorAll('.adjust-balance');
    if (balanceBtns) {
        balanceBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const userId = this.dataset.userId;
                const username = this.dataset.username;
                const currentBalance = parseFloat(this.dataset.balance);

                const amount = prompt(`当前用户 ${username} 余额：¥${currentBalance.toFixed(2)}\n请输入调整金额（正数增加，负数减少）：`);
                if (amount === null) return;

                // 验证金额格式
                if (!/^[-]?\d+(\.\d{1,2})?$/.test(amount)) {
                    adminToast('请输入正确的金额格式（最多2位小数）', false);
                    return;
                }

                const adjustAmount = parseFloat(amount);
                if (currentBalance + adjustAmount < 0) {
                    adminToast('调整后余额不能为负数', false);
                    return;
                }

                fetch('/admin/api/user/adjust_balance', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: userId,
                        amount: adjustAmount
                    })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        adminToast('余额调整成功');
                        // 更新页面余额显示
                        const balanceElem = this.closest('tr').querySelector('.user-balance');
                        balanceElem.textContent = (currentBalance + adjustAmount).toFixed(2);
                        this.dataset.balance = (currentBalance + adjustAmount).toFixed(2);
                    } else {
                        adminToast('调整失败：' + data.msg, false);
                    }
                });
            });
        });
    }
});