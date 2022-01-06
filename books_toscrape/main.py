import requests
import pandas as pd
import shutil
from tqdm import tqdm
from bs4 import BeautifulSoup
from pathlib import Path

main_url = 'https://books.toscrape.com/'
page = requests.get(main_url)
main_soup = BeautifulSoup(page.text, 'html.parser')
images_folder = Path.cwd().joinpath('images')
if not images_folder.exists():
    images_folder.mkdir()

with pd.ExcelWriter(Path.cwd().joinpath('books.xlsx'), engine='xlsxwriter') as writer:
    for category in tqdm(main_soup.find('div', 'side_categories').find_all('a')):
        if category.text.strip() == 'Books':
            continue
        table = {
            'Image URL': [],
            'Title': [],
            'UPC': [],
            'Rating': [],
            'Price/Tax': [],
            'Availability': [],
            'Description': []
        }
        category_name = category.text.strip()
        category_url = main_url + category['href']
        category_images_folder = Path.cwd().joinpath('images', category_name)
        if not category_images_folder.exists():
            category_images_folder.mkdir()
        stop_flag = False
        while not stop_flag:
            category_page = requests.get(category_url)
            category_soup = BeautifulSoup(category_page.text, 'html.parser')
            book_links = [main_url + 'catalogue/' + link.a['href'].replace('../', '') for link in category_soup.find_all('h3')]
            for link in book_links:
                book_page = requests.get(link)
                book_soup = BeautifulSoup(book_page.text, 'html.parser')
                title = book_soup.h1.text
                image_url = main_url + book_soup.find('div', class_='item active').img['src'].replace('../', '')
                image_path = Path.cwd().joinpath('images', category_name, image_url.split('/')[-1])
                table_data = book_soup.find('table', 'table table-striped').find_all('td')
                upc = table_data[0].text
                price_incl_tax = table_data[3].text[1:]
                tax = table_data[4].text[1:]
                availability = table_data[5].text
                rating = book_soup.find('p', class_='star-rating').attrs['class'][1]
                description = book_soup.find('article', class_="product_page").find_all('p')[3].text

                response = requests.get(image_url, stream=True)
                with open(image_path, 'wb') as out_file:
                    shutil.copyfileobj(response.raw, out_file)

                table['Image URL'].append(Path(*image_path.parts[-3:]))
                table['Title'].append(title)
                table['UPC'].append(upc)
                table['Price/Tax'].append('/'.join([price_incl_tax, tax]))
                table['Availability'].append(availability)
                table['Rating'].append(rating)
                table['Description'].append(description)

            next_button = category_soup.find('li', class_='next')
            if next_button:
                category_url = category_url.split('/')
                category_url[-1] = next_button.a['href']
                category_url = '/'.join(category_url)
            else:
                stop_flag = True
        pd.DataFrame(table).to_excel(writer, sheet_name=category_name)
