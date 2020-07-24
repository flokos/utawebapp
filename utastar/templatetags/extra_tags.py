from django.template import Variable, VariableDoesNotExist , Library

register = Library()

#Template filter to access list elements by hard index(in a template)
@register.filter
def index(List, i):
    return List[int(i)]

#Template tag to get a range between 2 bounds(in a template) 	
@register.simple_tag 
def times(start,stop):
    return range(start,stop)

#Template tag to make multiplications inside the template
@register.simple_tag
def multiply(qty, unit_price):
    # you would need to do any localization of the result here
    return qty * unit_price

#Template tag to check if there is a utastar model for the specified research
@register.simple_tag
def check_results(research):
	utastar_model = research.utastar_model_set.all()
	if utastar_model:
		return True
	else:
		return False

#Template filter to add css classes to template arguments(those django passes to the template)		
@register.filter(name='addcss')
def addcss(field, css):
    attrs = {}
    definition = css.split(',')

    for d in definition:
        if ':' not in d:
            attrs['class'] = d
        else:
            t, v = d.split(':')
            attrs[t] = v

    return field.as_widget(attrs=attrs)