from django import forms


class RadioactiveDecayForm(forms.Form):
    N0 = forms.FloatField(label="Boshlang‘ich miqdor N0", initial=1000, min_value=0.000001)
    lambd = forms.FloatField(label="Parchalanish doimiysi λ (1/vaqt)", initial=0.2, min_value=0.000001)

    t_max = forms.FloatField(label="Maksimal vaqt (t_max)", initial=30, min_value=0.000001)
    steps = forms.IntegerField(label="Nuqtalar soni (steps)", initial=61, min_value=5, max_value=2000)
