import requests
from bs4 import BeautifulSoup
import csv

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

def get_caracteristiques(soup):
    try:
        header = soup.find('p', class_='ad-section-title', string='Caractéristiques :')
        if not header:
            raise NonValide("Les caractéristiques n'ont pas été trouvées dans l'annonce")
        ul = header.find_next('ul', class_='list-inline')
        return ul
    except AttributeError:
        raise NonValide("Les caractéristiques n'ont pas été trouvées dans l'annonce")

def extract_caracteristique(ul, label):
    try:
        for li in ul.find_all('li'):
            if label in li.text:
                return li.find_all('span')[1].text.strip()
        return "-"
    except AttributeError:
        return "-"

def type(soup):
    ul = get_caracteristiques(soup)
    type_texte = extract_caracteristique(ul, 'Type')
    if type_texte not in ['Maison', 'Appartement']:
        raise NonValide("Le type n'est ni 'Maison' ni 'Appartement'")
    return type_texte

def surface(soup):
    ul = get_caracteristiques(soup)
    return extract_caracteristique(ul, 'Surface')

def nbrpieces(soup):
    ul = get_caracteristiques(soup)
    return extract_caracteristique(ul, 'Nb. de pièces')

def nbrchambres(soup):
    ul = get_caracteristiques(soup)
    return extract_caracteristique(ul, 'Nb. de chambres')

def nbrsdb(soup):
    ul = get_caracteristiques(soup)
    return extract_caracteristique(ul, 'Nb. de sales de bains')

def dpe(soup):
    ul = get_caracteristiques(soup)
    return extract_caracteristique(ul, 'Consommation d\'énergie (DPE)')

def informations(soup):
    try:
        ville_info = ville(soup)
        type_info = type(soup)
        surface_info = surface(soup)
        nbrpieces_info = nbrpieces(soup)
        nbrchambres_info = nbrchambres(soup)
        nbrsdb_info = nbrsdb(soup)
        dpe_info = dpe(soup)
        prix_info = prix(soup)
        
        return f"{ville_info},{type_info},{surface_info},{nbrpieces_info},{nbrchambres_info},{nbrsdb_info},{dpe_info},{prix_info}"
    except NonValide as e:
        raise NonValide(f"Annonce non conforme: {e}")

def scrape_annonces(base_url, pages):
    annonces = []
    urls_vues = set()  # Ensemble pour stocker les URLs des annonces
    for page in range(1, pages + 1):
        url = f"{base_url}/{page}"
        print(f"Scraping page: {page}")  # Impression pour vérifier que nous parcourons toutes les pages
        soup = getsoup(url)
        links = soup.select('a[href^="/annonce-"]')
        print(f"Nombre de liens trouvés sur la page {page}: {len(links)}")  # Impression pour vérifier le nombre de liens trouvés
        for link in links:
            annonce_url = link['href']
            if not annonce_url.startswith('http'):
                annonce_url = f"https://www.immo-entre-particuliers.com{annonce_url}"
            if annonce_url not in urls_vues:  # Vérifier si l'URL a déjà été vue
                urls_vues.add(annonce_url)  # Ajouter l'URL à l'ensemble
                print(f"Traitement de l'URL: {annonce_url}")  # Impression pour vérifier l'URL traitée
                annonce_soup = getsoup(annonce_url)
                try:
                    info = informations(annonce_soup)
                    annonces.append(info)
                    print(f"Annonce ajoutée: {info}")  # Impression pour vérifier que l'annonce est ajoutée
                except NonValide as e:
                    print(f"Annonce non conforme: {e}")
        print(f"Nombre total d'annonces après la page {page}: {len(annonces)}")  # Impression pour vérifier le nombre total d'annonces après chaque page
    return annonces

def save_to_csv(filename, annonces):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Ville', 'Type', 'Surface', 'NbrPieces', 'NbrChambres', 'NbrSdb', 'DPE', 'Prix']
        writer = csv.writer(csvfile)
        writer.writerow(fieldnames)
        for annonce in annonces:
            writer.writerow(annonce.split(','))
            print(f"Annonce enregistrée: {annonce}")  # Impression pour vérifier que l'annonce est enregistrée

# Exemple d'utilisation
base_url = "https://www.immo-entre-particuliers.com/annonces/france-ile-de-france"
pages = 281  # Nombre de pages à parcourir
annonces = scrape_annonces(base_url, pages)
save_to_csv('annonces_ile_de_france.csv', annonces)
