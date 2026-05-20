from django import forms
from .models import ShippingAddress
class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, label="Full Name")
    email = forms.EmailField(label="Email")
    subject = forms.ChoiceField(choices=[
        ('order', 'Order Inquiry'),
        ('return', 'Return/Exchange'),
        ('other', 'Other')
    ], label="Subject")
    message = forms.CharField(widget=forms.Textarea, label="Message")


class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ['first_name', 'last_name', 'address1', 'address2', 'city', 'province', 'postal_code', 'phone_number', 'country']
      