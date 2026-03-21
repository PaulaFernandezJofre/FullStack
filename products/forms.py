"""
Forms para Productos
"""

from django import forms
from .models import Product, Tag


class ProductForm(forms.ModelForm):
    """Formulario para crear/editar productos."""
    
    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'short_description', 'description',
            'price', 'category', 'demo_url', 'file',
            'product_type', 'version', 'thumbnail'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'nombre-del-producto'
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción corta (máx. 300 caracteres)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Descripción detallada del producto'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'demo_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://demo.ejemplo.com'
            }),
            'version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1.0.0'
            }),
            'product_type': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError('El precio no puede ser negativo.')
        return price
