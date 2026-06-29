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