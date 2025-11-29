// 等待页面 DOM 加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 1. 通用提示函数（全局复用）
    window.showToast = function(msg, isSuccess = true) {
        // 创建提示框元素
        const toast = document.createElement('div');
        toast.style.position = 'fixed';
        toast.style.top = '20px';
        toast.style.left = '50%';
        toast.style.transform = 'translateX(-50%)';
        toast.style.padding = '10px 20px';
        toast.style.borderRadius = '4px';
        toast.style.color = 'white';
        toast.style.zIndex = '9999';
        toast.style.transition = 'opacity 0.3s, transform 0.3s';
        // 成功绿色，失败红色
        toast.style.backgroundColor = isSuccess ? '#48bb78' : '#e53e3e';
        toast.textContent = msg;

        // 添加到页面
        document.body.appendChild(toast);

        // 3秒后自动消失
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 3000);
    };

    // 2. 检查登录状态（需要后端配合返回登录状态）
    window.checkLogin = function() {
        const username = sessionStorage.getItem('username');
        const loginBtn = document.querySelector('.login-btn');
        const registerBtn = document.querySelector('.register-btn');
        const userCenterBtn = document.querySelector('.user-center-btn');
        
        if (username) {
            // 已登录：隐藏登录/注册，显示个人中心
            if (loginBtn) loginBtn.style.display = 'none';
            if (registerBtn) registerBtn.style.display = 'none';
            if (userCenterBtn) {
                userCenterBtn.style.display = 'inline-block';
                userCenterBtn.textContent = `欢迎，${username}`;
            }
        } else {
            // 未登录：显示登录/注册，隐藏个人中心
            if (loginBtn) loginBtn.style.display = 'inline-block';
            if (registerBtn) registerBtn.style.display = 'inline-block';
            if (userCenterBtn) userCenterBtn.style.display = 'none';
        }
    };

    // 3. 退出登录功能
    const logoutBtn = document.querySelector('.logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            fetch('/api/user/logout', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        sessionStorage.removeItem('username');
                        sessionStorage.removeItem('user_id');
                        showToast('退出登录成功');
                        setTimeout(() => window.location.reload(), 1000);
                    } else {
                        showToast('退出失败：' + data.msg, false);
                    }
                });
        });
    }

    // 初始化：检查登录状态
    checkLogin();
});