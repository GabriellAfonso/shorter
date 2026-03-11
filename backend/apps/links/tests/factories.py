import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from apps.links.models.link_click import LinkClick
from apps.links.models.short_url import ShortURL
from apps.accounts.tests.factories import UserFactory


class ShortURLFactory(DjangoModelFactory):
    class Meta:
        model = ShortURL

    original_url = factory.Faker("url")
    slug = factory.Sequence(lambda n: f"test{n:04d}")
    title = factory.Faker("sentence", nb_words=4)
    owner = factory.SubFactory(UserFactory)
    is_active = True


class ExpiredShortURLFactory(ShortURLFactory):
    expires_at = factory.LazyFunction(lambda: timezone.now() - timezone.timedelta(hours=1))


class LinkClickFactory(DjangoModelFactory):
    class Meta:
        model = LinkClick

    link = factory.SubFactory(ShortURLFactory)
    ip_address = "hashed_ip_abc123"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0"
    referrer = "https://google.com"
    browser = "Chrome"
    os = "Windows"
    device_type = "desktop"
