document.addEventListener('DOMContentLoaded', function() {
    // 1. 通用提示函数
    window.adminToast = function(msg, isSuccess = true) {
        const toast = document.createElement('div');
        toast.style.position = 'fixed';
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.padding = '12px 20px';
        toast.style.borderRadius = '4px';
        toast.style.color = 'white';
        toast.style.zIndex = '9999';
        toast.style.transition = 'all 0.3s';
        toast.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
        toast.style.backgroundColor = isSuccess ? '#3b82f6' : '#ef4444';
        toast.textContent = msg;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-10px)';
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 3000);
    };

    // 2. 侧边栏当前页面激活
    const currentPath = window.location.pathname;
    const sidebarLinks = document.querySelectorAll('.sidebar-menu a');
    sidebarLinks.forEach(link => {
        if (link.pathname === currentPath) {
            link.classList.add('active');
        }
    });

    // 3. 退出登录功能
    const logoutBtn = document.querySelector('.admin-logout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            if (confirm('确定要退出后台管理系统吗？')) {
                fetch('/admin/logout', { method: 'POST' })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            window.location.href = '/admin/login';
                        } else {
                            adminToast('退出失败：' + data.msg, false);
                        }
                    });
            }
        });
    }
});