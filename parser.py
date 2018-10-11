import time
import urllib.request
from typing import List
import gspread
import requests
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials


site_link = 'https://yessport.co.uk'


def create_link_for_site_parse(text_for_search):
    return 'https://yessport.co.uk/search.php?text=' + text_for_search.replace(' ', '+')


def get_product_items(user_input: str) -> List:
    products_items_storage = []  # список
    try:
        html = reading_html_pages(create_link_for_site_parse(user_input))
        page_count = count_page_numbers(html)  # отримання кількості сторінок
        print("Усього сторінок", page_count)  # кількість сторінок з товаром
        # check for page_counter
        if page_count > 0:  # ксть сторінок більша від 0, то
            for numbers_page in range(0, page_count):  # проход всіх сторінок
                new_list_goods = reading_html_pages(create_link_for_site_parse(user_input))
                # додавання сторінок
                products_items_storage.extend(parsing_html_page(new_list_goods + '&counter=%d' % numbers_page))

            for products_storage in products_items_storage:
                print(products_storage)
        else:
            new_parse_link = create_link_for_site_parse(user_input)
            html = reading_html_pages(new_parse_link)
            products_items_storage.extend(parsing_html_page(html))
        print('Усього товару найдено: ', len(products_items_storage))
        return products_items_storage
    except AttributeError:
        print("Товару '" + user_input + "' немає!")
    except UnicodeEncodeError:
        print("Товару '" + user_input + "' немає!")


def reading_html_pages(url):
    response = urllib.request.urlopen(url)
    return response.read()


def count_page_numbers(html):  # пошук кількості сторінок
    soup = BeautifulSoup(html, 'lxml')
    paging_setting_top = soup.find('div', id="paging_setting_top")  # пошук сторінок
    div_search = paging_setting_top.find('div', class_="search_paging_sub")
    if div_search is None:
        return 0
    a_paging = div_search.find_all('a', class_='paging')[-1].text  # провірка на кількість сторінок
    return int(a_paging)  # повернення числа кількості сторінок


def parsing_html_page(html):  # парсер сайту
    products_items_storage = []  # пустий список
    soup = BeautifulSoup(html, 'lxml')
    div_search = soup.find('div', id="search")

    for selection_items in div_search.find_all('div'):  # перебор всіх елементів з div
        column = selection_items.find_all('div')
        for cols in column:
            title_cols = cols.find_all('a', class_='product-icon align_row')  # вхід в тег А
            for title_col in title_cols:
                alt_img = title_col.find_all('img')  # все що після img
                a_href = title_col.attrs['href']  # відокремлене все після хреф
                links = site_link + a_href  # силка на товар
                inf_pars = BeautifulSoup(reading_html_pages(links), 'lxml')  # парсинг кожного товару
                divs = inf_pars.find_all('div', id='content')

                for div_photo in divs:
                    # ліва колока
                    photo_content = div_photo.find_all('div', class_='photos col-md-8 col-sm-6 col-xs-12 ')
                    # права колонка
                    product_inf = div_photo.find_all('div', class_='product_info col-md-4 col-sm-6 col-xs-12 ')

                    for selects_button in product_inf:  # розмір взуття
                        select_button = selects_button.find_all('div', class_='product_section_sub')
                        size_number = []
                        for size_products in select_button:
                            size = size_products.find_all('a', class_='select_button')
                            for proportions in size:
                                length_content = proportions.contents
                                if len(str(length_content[0])) < 20:
                                    for list_size in length_content:
                                        size_number.append(list_size)
                                my_size = '; '.join(size_number)

                    for informs in product_inf:
                        product_code = informs.find('strong')  # код
                        products_codes = product_code.contents

                    for a_href in photo_content:  # фотки
                        img_url = a_href.find_all('a', class_='projector_medium_image')
                        photo_list_items = []
                        for link_photos in img_url:
                            link_photo = link_photos.attrs['href']  # фотки всі
                            photo_list_items.append(link_photo)
                        my_photo = site_link+';  https://yessport.co.uk'.join(photo_list_items)  # розділ списку фоток

                headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                         'Chrome/67.0.3396.99 Safari/537.36', 'Accept-Encoding': 'identity'}
                money = ["GBP", "EUR", "USD"]
                currency_value = []
                for currency in money:
                    cookie = {'CURRID': currency}
                    url_parse = "{0}?curr={1}".format(links, currency)
                    res = requests.get(url_parse, cookies=cookie, headers=headers)
                    soup = BeautifulSoup(res.text, 'html.parser')
                    name_box = soup.find_all(attrs={'id': 'projector_price_value'})
                    currency_value.append(name_box)
                currencies = []
                for value in currency_value:
                    for price_value in value:
                        currency_price = price_value.contents
                        for price_eur in currency_price:
                            currencies.append(price_eur.replace('\xa0', ''))
                for photo_link in alt_img:  # формування парсингу
                    for individual_number in products_codes:
                        currency = '; '.join(currencies)
                        products_items_storage.append({'Name': photo_link.attrs['alt'], 'Size': my_size,
                                                       'Product code': individual_number, 'Price': currency,
                                                       'Image': my_photo, 'Link': links})

    for project in products_items_storage:
        print(project)

    return products_items_storage


def filling_tables_product_data(products_items_storage):
   # JSON ФАЙЛА КЛЮЧА
    json_file_key = \
    {
        "type": "service_account",
        "project_id": "elated-unity-213115",
        "private_key_id": "aa33948ffb3c32dbafbc62d93c73dbd8d451a3b3",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCoX8LyjzCwkRoS\n"
                       "3pbCKN/yAu5stDaB5/Qual6xJOoWaJwP0rlyaIlB+R9aXSMBr76pqHN3g3TBPMB6\ngNzSxIaTc5gyONxBp/UfnYNycQ+5"
                       "yXlgvzhgi7I9v1lUcPZPl7k9zOC8G4+Q6a04\nnifp+9mQB0RxQDw5Dt8HgZPm2dXEOBCKyPuP5ShhOkMisaQLXBbqc9jeV"
                       "OS+d5Jc\n5quxYOxaKwsjNkFWNAJ5NSak60uCZpcFiBI2CW9S7/vHM9hNNtnEMmV65YwSVl7B\nZBTgfMhSqgRXI9s02Tp3"
                       "lt80AGLuRyWvbTgUcDT7dqaEID5XTyAGPUBesb3Ym/H2\nENwzQGBzAgMBAAECggEASv+czn6JqZx4iL8tV/7tAdfca/856"
                       "FNxqNsooq9WtfSS\nz1mF0ThPK1vUY2PpG+80dk3aYPnlH833zplnw1pWt4dd28EIGxa9UP/QdUF3R8I+\nlqGWcyrGkkqR"
                       "d9N5Y6qpkKWZ1TBRmrL7vaR1EvxjxIv4KJn8OU4ueiF1x/ZwCZ5W\nhskUtZ8Xpk46k5WOYyDiu0zkqPTfzpqnsaOYqPT28"
                       "zgP+uZjp70OSYBblhXiDDBL\nM89NohO/buoNdwfdruD2ySXksB6uqiRGnipaRcjUpGg7C6sOROoA9p61/kRD8al3\nysaa"
                       "Y9VNB/ueqhTLO7ls9/Il7pt8ltxW83HfzQ7jwQKBgQDSX36M8KqW1C/3fr0w\nKE4JRNOmFBMKrTSQ8t2ekGVmhc5dN/l+6"
                       "K8egkvUaN436YpVxA1JBCt9IRHfpX6V\nYQ+JJiuTwD2fGfw4svc1JUi2g9Ft4HI8mBU0JQO41nLZJ+f+B0zIYRIj18Svhw"
                       "9v\ns0dAxLlC+r9iGIiGZhCv8ocyVQKBgQDM5F3Du5vUON8STpLZHcgyTU1qF45QvcEX\nVd8l2qL8iEBO5sL7IWS0wxPuf"
                       "HEMSF7kH1ybKQPjKHQit4PUgfLtv6kcCr6qvEXL\n9FGUT+hHkmYY/XsFZDepJk8gx4oC0AF7zpYc9xImfaE1lol/2cy5bg"
                       "CbGE5OHpFw\nnZqO5t1fpwKBgQCbHB/RySzuMpr/T6osVLtc6CtpW4nCqHyGlxtCa1LoaaYDY18I\n7IUZ6JYCkiOuc/o0T"
                       "G5DNNjf1L859+rCNyNeSw98TBTjNySZpZLR06CuObjz27Y+\n6R9RKC17XlqltF/AFB/P6oqWdOOnS9zczgGuRp4WPY1YxZ"
                       "/8AEszf42hVQKBgCnN\ncd/sV/etfr2icE2ByQWSRfgeRDfu7wVOzM9RUy2Isu4mIKPSBVTn9BoVI49o+Is8\nZs11Sci/y"
                       "SoIHQpvVNvy3ZLOEmaNMQRSnY5P20k28kOo+7922fBV05ERhPPb8mGL\nHY9dTUOzH//p7bW6/wzaB5+dDuTbUbsTPKRpL8"
                       "NDAoGBAKrj2/nZU6r7QD1A9l25\nflHie/vJK9ylBnLmNhAypCZc9IY5rA35HxHQ3X+M1LBpt3SZubh4//p2gdOZ/N1b\nd"
                       "e/kkSmLMnXoWKOCWYzsDlUuPClJ9UvMwgG0c1fqwfEBtoILlz4h3ez+YNhKAuOa\nuFGBnkk2CbvMqj/mN2W4g1JV\n----"
                       "-END PRIVATE KEY-----\n",
        "client_email":
            "shoose-account@elated-unity-213115.iam.gserviceaccount.com",
        "client_id": "114212733795504379299",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/shoose-account%40elated-unity-2131"
                                "15.iam.gserviceaccount.com"
    }

    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    authorization = ServiceAccountCredentials.from_json_keyfile_dict(json_file_key, scope)  # Авторизация данных
    client = gspread.authorize(authorization)  # Получение token'a для редактирование/чтения таблицы

    fill_sheet = client.open("yessport").sheet1  # загружаем таблицу
    list_items = products_items_storage  # список з елементів
    table_header_name = ["Ім'я", "Код", "Розмір", "Ціна", "Фотографія", "Посилання"]  # заголовок

    row_title = fill_sheet.row_values(1)
    if row_title != table_header_name:
        fill_sheet.delete_row(1)
        fill_sheet.insert_row(table_header_name, 1)  # дододавання заголовку в перший рядок

    product_code = []
    full_product = []
    for line, value in enumerate(list_items, 2):
        full_name_product = [value['Name'], value['Product code'], value['Size'], value['Price'], value['Image'],
                             value['Link']]
        full_product.append(full_name_product)
        product_code.append(value['Product code'])

    available_codes = fill_sheet.col_values(2)[1::]  # наявні коди в таблиці
    no_codes = []  # відсутні коди в таблиці
    for code in product_code:
        if code not in available_codes:
            no_codes.append(code)
    final_fill = []
    for product in full_product:
        for me in no_codes:
            if me in product:
                final_fill.append(product)
    for new_table_data in final_fill:
        time.sleep(1.5)
        fill_sheet.append_row(new_table_data)


user = input("text: ")  # uncomment for testing
products_items = get_product_items(user)
# filling_tables_product_data(products_items)

