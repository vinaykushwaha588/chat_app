from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry
from .models import FakeUserData  # Make sure it's the correct model

# Define the index
fakeuser_index = Index("fakeusers")

# Optional index settings
fakeuser_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)

@registry.register_document
class FakeUserDocument(Document):
    first_name = fields.TextField()
    last_name = fields.TextField()
    email = fields.TextField()
    phone = fields.TextField()
    age = fields.IntegerField()
    gender = fields.TextField()

    class Index:
        name = "fakeusers"  

    class Django:
        model = FakeUserData