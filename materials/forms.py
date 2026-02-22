"""materials forms.

Hozircha minimal forma namunasi.
"""

from django import forms


class ExampleForm(forms.Form):
    title = forms.CharField(label="Sarlavha", max_length=200, required=False)
