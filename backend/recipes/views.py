from django.http import Http404
from django.shortcuts import get_object_or_404, redirect

from recipes.models import Recipe


def short_link_redirect(request, code):
    try:
        recipe_id = int(code, 36)
    except ValueError:
        raise Http404('Некорректная короткая ссылка.')
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    return redirect(f'/recipes/{recipe.pk}/')
