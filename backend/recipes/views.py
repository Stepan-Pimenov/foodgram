from django.http import HttpResponsePermanentRedirect

from recipes.models import Recipe


def short_link_redirect(request, code):
    try:
        recipe = Recipe.objects.get(pk=int(code, 36))
    except (ValueError, Recipe.DoesNotExist):
        return HttpResponsePermanentRedirect(
            request.build_absolute_uri('/not_found')
        )
    return HttpResponsePermanentRedirect(
        request.build_absolute_uri(f'/recipes/{recipe.pk}/')
    )
