import requests
from bs4 import BeautifulSoup
import csv
import pandas as pd

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
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['Ville', 'Type', 'Surface', 'NbrPieces', 'NbrChambres', 'NbrSdb', 'DPE', 'Prix']
        writer = csv.writer(csvfile)
        writer.writerow(fieldnames)
        for annonce in annonces:
            writer.writerow(annonce.split(','))
            print(f"Annonce enregistrée: {annonce}")  # Impression pour vérifier que l'annonce est enregistrée



# ==================== NETTOYAGE DES DONNÉES ====================

# Importer le contenu du CSV dans un DataFrame nommé annonces
annonces = pd.read_csv('annonces_ile_de_france.csv')
# Remplacer les valeurs manquantes dans 'DPE' par la valeur 'Vierge'
annonces['DPE'] = annonces['DPE'].replace('-', 'Vierge')
# Convertir les colonnes 'Surface', 'NbrPieces', 'NbrChambres', 'NbrSdb' en float
annonces['Surface'] = annonces['Surface'].str.replace(' m²', '').str.replace(' ', '').replace('-', None).astype(float)
annonces['NbrPieces'] = annonces['NbrPieces'].replace('-', None).astype(float)
annonces['NbrChambres'] = annonces['NbrChambres'].replace('-', None).astype(float)
annonces['NbrSdb'] = annonces['NbrSdb'].replace('-', None).astype(float)
# Remplacer les valeurs manquantes par la moyenne de chaque colonne
annonces['Surface'] = annonces['Surface'].fillna(annonces['Surface'].mean())
annonces['NbrPieces'] = annonces['NbrPieces'].fillna(annonces['NbrPieces'].mean())
annonces['NbrChambres'] = annonces['NbrChambres'].fillna(annonces['NbrChambres'].mean())
annonces['NbrSdb'] = annonces['NbrSdb'].fillna(annonces['NbrSdb'].mean())
# Supprimer les lignes restantes avec des valeurs manquantes si nécessaire
annonces = annonces.dropna()
# Utiliser la méthode des variables indicatrices pour les colonnes 'Type' et 'DPE'
annonces = pd.get_dummies(annonces, columns=['Type', 'DPE'])
# Sauvegarder les données modifiées dans un nouveau fichier CSV
annonces.to_csv('annonces_ile_de_france_final.csv', index=False)
print("Données nettoyées et sauvegardées dans 'annonces_ile_de_france_final.csv'")


# ==================== TRAITEMENT DES VILLES ====================

# QUESTION 12 : Importation dans un DataFrame nommé villes 
villes = pd.read_csv('cities.csv')
# QUESTION 13 : Importation dans un DataFrame nommé villes

# Convertir en minuscules
annonces['Ville'] = annonces['Ville'].str.lower()
villes['label'] = villes['label'].str.lower()

# Supprimer espaces, tirets, apostrophes
annonces['Ville'] = annonces['Ville'].str.replace(" ", "", regex=False)
annonces['Ville'] = annonces['Ville'].str.replace("-", "", regex=False)
annonces['Ville'] = annonces['Ville'].str.replace("'", "", regex=False)

villes['label'] = villes['label'].str.replace(" ", "", regex=False)
villes['label'] = villes['label'].str.replace("-", "", regex=False)
villes['label'] = villes['label'].str.replace("'", "", regex=False)

# Suppression des accents
accents = {"É": "e","é": "e", "è": "e", "ê": "e", "à": "a", "â": "a", "ç": "c", "ù": "u", "ô": "o", "î": "i", "ï": "i", "ÿ": "y"}
for accent, non_accent in accents.items():
    annonces['Ville'] = annonces['Ville'].str.replace(accent, non_accent, regex=False)
    villes['label'] = villes['label'].str.replace(accent, non_accent, regex=False)

# Remplacer uniquement "Saint-" au début du nom de la ville
annonces['Ville'] = annonces['Ville'].str.replace("saint", "st", regex=False)
villes['label'] = villes['label'].str.replace("saint", "st", regex=False)
annonces['Ville'] = annonces['Ville'].replace("sts", "beautheilsts")

# Cas particuliers
annonces['Ville'] = annonces['Ville'].replace({
    'lechesnayrocquencourt': 'lechesnay',
    'eragnysuroise': 'eragny',
    'evrycourcouronnes': 'courcouronnes'
})
villes['label'] = villes['label'].replace({
    'lechesnayrocquencourt': 'lechesnay',
    'eragnysuroise': 'eragny',
    'evrycourcouronnes': 'courcouronnes'
})

# Arrondissements de Paris
def gerer_arrondissements_paris(nom):
    if 'paris' in nom and ('eme' in nom or 'er' in nom):
        return 'paris'
    return nom
annonces['Ville'] = annonces['Ville'].apply(gerer_arrondissements_paris)

#==================== JOINTURES DES DEUX TABLES ====================
# Supprimer les doublons dans villes pour s'assurer qu'il y a une seule correspondance par ville
villes_unique = villes[['label', 'latitude', 'longitude']].drop_duplicates(subset=['label'])
# Fusionner uniquement sur 'latitude' et 'longitude'
annonces = annonces.merge(
    villes_unique, 
    left_on='Ville', 
    right_on='label', 
    how='left'
)
# Supprimer la colonne 'label' et 'Ville' qui ne sert plus
annonces = annonces.drop(columns=['Ville', 'label'])
# Sauvegarde du fichier nettoyé
annonces.to_csv('annonces_ile_de_france_final.csv', index=False)
