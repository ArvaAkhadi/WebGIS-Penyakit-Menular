/* =========================================================
   AUTH HELPER
   ========================================================= */
window.Auth = {
  SESSION_KEY: 'adminSession',
  SESSION_TTL: 24 * 60 * 60 * 1000,   // 24 jam

  getSession() {
    try {
      const raw = localStorage.getItem(this.SESSION_KEY);
      if (!raw) return null;
      const s = JSON.parse(raw);
      if (Date.now() - s.loginAt > this.SESSION_TTL) {
        localStorage.removeItem(this.SESSION_KEY);
        return null;
      }
      return s;
    } catch (e) { return null; }
  },

  isAdmin() { return !!this.getSession(); },

  login(sessionData) {
    localStorage.setItem(this.SESSION_KEY, JSON.stringify({
      ...sessionData,
      loginAt: Date.now()
    }));
  },

  logout() {
    localStorage.removeItem(this.SESSION_KEY);
    window.location.href = 'index.html';
  },

  requireAdmin() {
    if (!this.isAdmin()) {
      window.location.href = 'login.html';
      return false;
    }
    return true;
  },

  /* Render tombol admin / user di panel map */
  applyToPanel() {
    const adminActions = document.getElementById('admin-actions');
    const userActions  = document.getElementById('user-actions');
    const welcomeBox   = document.getElementById('welcome-box');

    if (this.isAdmin()) {
      if (adminActions) adminActions.style.display = 'flex';
      if (userActions)  userActions.style.display  = 'flex';
      const s = this.getSession();
      if (welcomeBox) {
        welcomeBox.innerHTML =
          '<div style="font-size:11px;color:#0a2a5c;padding:6px 10px;' +
          'background:#e7f3ff;border-radius:6px;margin-bottom:8px;">' +
          '<i class="fas fa-user-shield"></i> Login sebagai: <b>' +
          (s.nama || s.username) + '</b>' +
          '<a href="#" onclick="Auth.logout();return false;" ' +
          'style="float:right;color:#c0392b;font-size:10px;text-decoration:none;">' +
          '<i class="fas fa-sign-out-alt"></i> Logout</a></div>';
      }
    } else {
      if (adminActions) adminActions.style.display = 'none';
      if (userActions)  userActions.style.display  = 'flex';
      if (welcomeBox)   welcomeBox.innerHTML = '';
    }
  }
};