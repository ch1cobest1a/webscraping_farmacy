from django import forms

class ScraperForm(forms.Form):
    PHARMACY_CHOICES = [
        ('Salcobrand', 'Salcobrand'),
        # Agrega más farmacias si es necesario
    ]

    CATEGORY_CHOICES = [
        ('Medicamento', 'Medicamento'),
        # Agrega más categorías si es necesario
    ]

    pharmacy = forms.ChoiceField(choices=PHARMACY_CHOICES, label="Farmacia")
    category = forms.ChoiceField(choices=CATEGORY_CHOICES, label="Categoría")
