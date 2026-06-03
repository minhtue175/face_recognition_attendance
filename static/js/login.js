// static/js/login.js

// Chuyển đổi vai trò
document.querySelectorAll('.role-tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.role-tab').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('role-field').value = btn.dataset.role;
  });
});

// Hiện/ẩn mật khẩu
function togglePw() {
  const pw = document.getElementById('password');
  pw.type = pw.type === 'password' ? 'text' : 'password';
}