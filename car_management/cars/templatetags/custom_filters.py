# cars/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter(name='add_suffix')
def add_suffix(value, suffix):
    """Add a suffix to the value."""
    return str(value) + str(suffix)
