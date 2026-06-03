from django import forms
from .models import User

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mật khẩu'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Xác nhận mật khẩu'}))

    class Meta:
        model = User
        # Chú ý: Dùng đúng chữ 'Role' viết hoa và 'password' mặc định
        fields = ['username', 'email', 'Role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên đăng nhập'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'Role': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Mật khẩu xác nhận không khớp!")
        return cleaned_data

    def save(self, commit=True):
        # Nắm lấy object user nhưng chưa lưu vội
        user = super().save(commit=False)
        # Sử dụng hàm set_password của Django để băm (hash) mật khẩu tự động
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user