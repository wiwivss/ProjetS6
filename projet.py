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
        prix_numerique = int(prix_texte.replace('€', '').replace(' ', ''))
        if prix_numerique < 10000:
            raise NonValide("Prix trop bas, probablement une annonce non valide")
        return str(prix_numerique)
    except AttributeError:
        raise NonValide("Le prix n'a pas été trouvé dans l'annonce")
    

def ville(soup):
    try:
        # Ajuster le sélecteur en fonction de la structure HTML réelle
        details_texte = soup.select_one('.product-identity-container').text.strip()
        # Trouver la dernière occurrence de ", " et extraire la ville
        index = details_texte.rfind(", ")
        if index == -1:
            raise NonValide("La ville n'a pas été trouvée dans l'annonce")
        ville_texte = details_texte[index + 2:]  # +2 pour sauter ", "
        return ville_texte
    except AttributeError:
        raise NonValide("La ville n'a pas été trouvée dans l'annonce")

# Exemple d'utilisation
url = "https://www.immo-entre-particuliers.com/annonce-alpes-maritimes-le-cannet/409275-villa-sur-les-hauteurs-de-golfe-juan-avec-une-vue-mer-panoramique"
soup = getsoup(url)
try:
    print(prix(soup))
except NonValide as e:
    print(e)

try:
    print(ville(soup))
except NonValide as e:
    print(e)