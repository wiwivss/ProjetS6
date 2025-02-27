import requests
from bs4 import BeautifulSoup

class NonValide(Exception):
    def __init__(self, message="L'annonce n'est pas valide"):
        self.message = message
        super().__init__(self.message)

def getsoup(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def prix(soup):
    try:
        prix_texte = soup.select_one('.product-price').text.strip()
        if not prix_texte:
            raise NonValide("Le prix n'a pas été trouvé dans l'annonce")
        prix_numerique = int(prix_texte.replace('€', '').replace(' ', ''))
        if prix_numerique < 10000:
            raise NonValide("Prix trop bas, probablement une annonce non valide")
        return str(prix_numerique)
    except (AttributeError, ValueError):
        raise NonValide("Le prix n'a pas été trouvé ou est invalide dans l'annonce")

def ville(soup):
    try:
        details_texte = soup.select_one('h2.mt-0').text.strip()
        index = details_texte.rfind(", ")
        if index == -1:
            raise NonValide("La ville n'a pas été trouvée dans l'annonce")
        ville_texte = details_texte[index + 2:]
        return ville_texte
    except AttributeError:
        raise NonValide("La ville n'a pas été trouvée dans l'annonce")


def get_caracteriques(soup):
    caracteriques = {}
    for caracterique in soup.select('row product-features my-3'):
        key = caracterique.select_one('.col-6').text.strip()
        value = caracterique.select_one('.col-6.text-right').text.strip()
        caracteriques[key] = value
    return caracteriques


    






# Exemple d'utilisation
url = "https://www.immo-entre-particuliers.com/annonce-loiret-la-chapelle-sur-aveyron/409230-grande-maison-familiale-de-247-m2-avec-jardin-grange-et-panneaux-solaires-au-coeur-du-village-de-la-chapelle-sur-aveyron-ecole-et-bus-scolaires-a-proximite"
soup = getsoup(url)
try:
    print(prix(soup))
except NonValide as e:
    print(e)

try:
    print(ville(soup))
except NonValide as e:
    print(e)

print(get_caracteriques(soup))



