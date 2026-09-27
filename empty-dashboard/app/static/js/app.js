/**
 * Nexus Enterprise Analytics Portal - Core Interaction Logic
 * Lightweight, Vanilla JavaScript without external dependencies.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Live UTC Timestamp in Topbar
    const liveTimestampEl = document.getElementById('liveTimestamp');
    if (liveTimestampEl) {
        const updateClock = () => {
            const now = new Date();
            const year = now.getUTCFullYear();
            const month = String(now.getUTCMonth() + 1).padStart(2, '0');
            const day = String(now.getUTCDate()).padStart(2, '0');
            const hours = String(now.getUTCHours()).padStart(2, '0');
            const minutes = String(now.getUTCMinutes()).padStart(2, '0');
            const seconds = String(now.getUTCSeconds()).padStart(2, '0');
            liveTimestampEl.textContent = `${year}-${month}-${day} ${hours}:${minutes}:${seconds} UTC`;
        };
        updateClock();
        setInterval(updateClock, 1000);
    }

    // 2. Auto-dismiss Flash Alerts
    const flashAlerts = document.querySelectorAll('.flash-messages-container .alert');
    flashAlerts.forEach((alert) => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-4px)';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });

    // 3. Mobile Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const appSidebar = document.getElementById('appSidebar');
    if (sidebarToggle && appSidebar) {
        sidebarToggle.addEventListener('click', () => {
            appSidebar.classList.toggle('open');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768 && 
                appSidebar.classList.contains('open') && 
                !appSidebar.contains(e.target) && 
                !sidebarToggle.contains(e.target)) {
                appSidebar.classList.remove('open');
            }
        });
    }

    // 4. Form Submit visual state
    const loginForm = document.querySelector('.login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = `
                    <span>Authenticating...</span>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
                        <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
                        <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"></path>
                    </svg>
                `;
            }
        });
    }
});
