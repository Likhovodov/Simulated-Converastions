from django import template

register = template.Library()

@register.filter(name='is_researcher')
def is_staff(user):
    return user.is_staff