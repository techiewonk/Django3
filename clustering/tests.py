import pytest
import os.path

from django.test import Client
from django.contrib.auth.models import User


@pytest.fixture
def make_file(tmpdir, format):
    filename = f'test.{format}'
    filepath = os.path.join(str(tmpdir), filename)
    with open(filepath, 'w') as file:
        file.write('')
    yield filepath


class TestAlgorithmView:
    @pytest.mark.django_db
    def test_get_for_authenticated_user(self, admin_client):
        response = admin_client.get('/clustering/')
        assert response.status_code == 200
        assert len(response.content) != 0

    def test_get_redirect_for_unauthenticated_user(self):
        c = Client(enforce_csrf_checks=True)
        response = c.get('/clustering/')
        assert response.status_code == 302
        assert response.url == '/accounts/login/?next=/clustering/'

    @pytest.mark.parametrize('filepath', ['./test/data/AB_NYC_2019.csv',
                                          './test/data/airbnb_ny_dropna.csv',
                                          './test/data/Airbnb_Texas_Rentals.csv',
                                          './test/data/Airbnb_Texas_Rentals_dropna.csv',
                                          './test/data/Airbnb_Texas_Rentals_dropna_new.csv',
                                          './test/data/geoflickr_spb.csv',
                                          './test/data/homegate_month_living_dropna.csv',
                                          './test/data/homegate_month_rooms_dropna.csv',
                                          ])
    def test_post_upload_file_update_form(self, admin_client, filepath):
        response = admin_client.post('/clustering/', data={'file': open(filepath, 'r'), '_upload': ''})
        assert response.status_code == 200
        assert response.content.find(b'<input type="number" name="k"') != -1
        assert response.content.find(b'<input type="number" name="eps"') != -1
        assert response.content.find(b'<select name="latitude"') != -1
        assert response.content.find(b'<select name="longitude"') != -1
        assert response.content.find(b'<select name="algorithm"') != -1
        assert response.content.find(b'<option value="k_mxt_w3">k-MXT-W</option>') != -1
        assert response.content.find(b'<option value="k_mxt">k-MXT</option>') != -1

    @pytest.mark.parametrize('filepath, features', [('./test/data/AB_NYC_2019.csv', 'price'),
                                                    ('./test/data/airbnb_ny_dropna.csv', 'price'),
                                                    ('./test/data/Airbnb_Texas_Rentals.csv', 'price'),
                                                    ('./test/data/Airbnb_Texas_Rentals_dropna.csv', 'price'),
                                                    ('./test/data/Airbnb_Texas_Rentals_dropna_new.csv', 'price'),
                                                    ('./test/data/homegate_month_living_dropna.csv', 'price'),
                                                    ('./test/data/homegate_month_rooms_dropna.csv', 'price'),
                                                    ])
    @pytest.mark.parametrize('algorithm', ['k_mxt_w3', 'k_mxt'])
    @pytest.mark.parametrize('k', [2, 3, 4])
    @pytest.mark.parametrize('eps', [0.1, 0.2, 0.25])
    def test_post_calculate(self, admin_client, filepath, k, eps, features, algorithm):
        response = admin_client.post('/clustering/', data={'file': open(filepath, 'r'), '_upload': ''})
        assert response.status_code == 200
        response = admin_client.post('/clustering/', data={'k': k,
                                                           'eps': eps,
                                                           'features': features,
                                                           'algorithm': algorithm,
                                                           '_calculate': '',
                                                           })
        assert response.status_code == 200

    @pytest.mark.parametrize('format', ['pdf', 'doc', 'py', 'js'])
    def test_post_upload_file_other_formats(self, admin_client, make_file, format):
        response = admin_client.post('/clustering/', data={'file': open(make_file, 'r'), '_upload': ''})
        assert response.status_code == 200
        assert response.content.find(b'<input type="file" class="custom-file-input" name="file" id="id_file"/>') != -1
        assert response.content.find(b'<input type="number" name="k"') == -1
        assert response.content.find(b'<input type="number" name="eps"') == -1
        assert response.content.find(b'<select name="latitude"') == -1
        assert response.content.find(b'<select name="longitude"') == -1
        assert response.content.find(b'<select name="algorithm"') == -1
        assert response.content.find(b'<option value="k_mxt_w3">k-MXT-W</option>') == -1
        assert response.content.find(b'<option value="k_mxt">k-MXT</option>') == -1


class TestUser:
    @pytest.mark.django_db
    @pytest.mark.parametrize('username, password', [('ns', 'qwerty'),
                                                    ('admin', 'admin'),
                                                    ('user', ''),
                                                    ('12345', 'qwerty'),
                                                    ('12345', '12345'),
                                                    ('1', 'qwerty'),
                                                    ('a', 'qwerty'),
                                                    ('!', 'qwerty'),
                                                    ('@', 'qwerty'),
                                                    ('@.^%&#@*_-+=)(', 'qwerty'),
                                                    ('qwerty', '@.^%&#@*_-+=)('),
                                                    ])
    def test_create_user(self, username, password):
        user = User.objects.create_user(username=username, password=password)
        user.save()
        c = Client(enforce_csrf_checks=True)
        assert c.login(username=username, password=password)
        c.logout()

    @pytest.mark.django_db
    @pytest.mark.parametrize('username, password', [('', 'qwerty'),
                                                    ('', ''),
                                                    ])
    def test_create_user_with_empty_username(self, username, password):
        with pytest.raises(ValueError):
            User.objects.create_user(username=username, password=password)
