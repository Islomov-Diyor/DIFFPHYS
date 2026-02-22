from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(label='Ismingiz', max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Ismingiz'
    }))
    telegram = forms.CharField(label='Telegram username', max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': '@username',
        'type': 'text'  # Bu MUHIM! Email emas!
    }))
    message = forms.CharField(label='Xabaringiz', widget=forms.Textarea(attrs={
        'class': 'form-control',
        'placeholder': 'Xabaringizni yozing...',
        'rows': 4
    }))
