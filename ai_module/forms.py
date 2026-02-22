from django import forms

class PronunciationForm(forms.Form):
    text = forms.CharField(
        label='Soʻz yoki gap kiriting',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masalan: Hello world'
        })
    )

class TextAnalysisForm(forms.Form):
    text = forms.CharField(
        label='Matn kiriting',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Masalan: This movie is amazing!',
            'rows': 4
        })
    )
from django import forms


class RadioactiveDecayForm(forms.Form):
    N0 = forms.FloatField(label="Boshlang‘ich miqdor N0", initial=1000, min_value=0.000001)
    lambd = forms.FloatField(label="Parchalanish doimiysi λ (1/vaqt)", initial=0.2, min_value=0.000001)

    t_max = forms.FloatField(label="Maksimal vaqt (t_max)", initial=30, min_value=0.000001)
    steps = forms.IntegerField(label="Nuqtalar soni (steps)", initial=61, min_value=5, max_value=2000)

from django import forms

class MassSpringForm(forms.Form):
    m = forms.FloatField(label="m (kg)", initial=1.0, min_value=0.0001)
    k = forms.FloatField(label="k (N/m)", initial=10.0, min_value=0.0001)
    c = forms.FloatField(label="c (N·s/m) — so‘nish", initial=0.0, min_value=0.0, required=False)

    x0 = forms.FloatField(label="x0 (m) — boshlang‘ich siljish", initial=0.1)
    v0 = forms.FloatField(label="v0 (m/s) — boshlang‘ich tezlik", initial=0.0)

    t_end = forms.FloatField(label="T (s) — vaqt oxiri", initial=10.0, min_value=0.0001)
    dt = forms.FloatField(label="dt (s) — qadam", initial=0.01, min_value=1e-6)

from django import forms

class RLCSeriesForm(forms.Form):
    R = forms.FloatField(label="R (Ohm)", initial=10.0, min_value=0.0)
    L = forms.FloatField(label="L (H)", initial=0.5, min_value=1e-9)
    C = forms.FloatField(label="C (F)", initial=0.01, min_value=1e-12)

    V0 = forms.FloatField(label="V0 (V) — manba kuchlanishi", initial=5.0)

    q0 = forms.FloatField(label="q0 (C) — boshlang‘ich zaryad", initial=0.0)
    i0 = forms.FloatField(label="i0 (A) — boshlang‘ich tok", initial=0.0)

    t_end = forms.FloatField(label="T (s) — vaqt oxiri", initial=10.0, min_value=1e-6)
    dt = forms.FloatField(label="dt (s) — qadam", initial=0.01, min_value=1e-6)


# ai_module/forms.py
from django import forms

class FreeFallDragForm(forms.Form):
    # Asosiy parametrlar
    m = forms.FloatField(label="m (kg)", initial=1.0, min_value=1e-9)
    g = forms.FloatField(label="g (m/s²)", initial=9.81, min_value=0.0)

    # Qarshilik turi va koeffitsient
    drag_type = forms.ChoiceField(
        label="Qarshilik turi",
        choices=[("linear", "Chiziqli: Fd = k·v"), ("quadratic", "Kvadratik: Fd = k·v²")],
        initial="linear"
    )
    k = forms.FloatField(label="k (qarshilik koeff.)", initial=0.2, min_value=0.0)

    # Boshlang'ich shartlar
    y0 = forms.FloatField(label="y0 (m) — boshlang'ich balandlik", initial=100.0)
    v0 = forms.FloatField(label="v0 (m/s) — boshlang'ich tezlik", initial=0.0)

    # Hisoblash sozlamalari
    t_end = forms.FloatField(label="T (s) — vaqt oxiri", initial=15.0, min_value=1e-6)
    dt = forms.FloatField(label="dt (s) — qadam", initial=0.02, min_value=1e-6)


from django import forms

class RadioactiveDecayForm(forms.Form):
    N0 = forms.FloatField(label="N0 (boshlang'ich miqdor)", initial=1000.0, min_value=1e-12)
    lam = forms.FloatField(label="λ (1/s)", initial=0.15, min_value=1e-12)
    t_end = forms.FloatField(label="T (s) — vaqt oxiri", initial=40.0, min_value=1e-6)
    dt = forms.FloatField(label="dt (s) — qadam", initial=0.05, min_value=1e-6)