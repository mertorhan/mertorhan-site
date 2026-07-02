from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message"]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Adınız",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-input",
                "placeholder": "ornek@eposta.com",
            }),
            "message": forms.Textarea(attrs={
                "class": "form-input form-textarea",
                "placeholder": "Mesajınız...",
            }),
        }

        # Kutuların altında gösterilecek Türkçe uyarılar
        error_messages = {
            "name": {"required": "Lütfen adınızı girin."},
            "email": {
                "required": "Lütfen e-posta adresinizi girin.",
                "invalid": "Lütfen geçerli bir e-posta adresi girin.",
            },
            "message": {"required": "Lütfen bir mesaj yazın."},
        }