import requests
from bs4 import BeautifulSoup


def get_yandex_reviews(restaurant_url):
    html_text = requests.get(restaurant_url).text
    soup = BeautifulSoup(html_text, 'html.parser')

    review_list = soup.find('div', {'class': 'business-reviews-card-view__reviews-container'})

    reviews = []
    items = review_list.find_all('div', {'class': ['business-reviews-card-view__review']})
    for i, item in enumerate(items):
        reviewer_name = item.find('div', {'class': 'business-review-view__author'}).find('a').text

        review_rate_number = 0
        review_rate_items = item.find('div', {'class': 'business-rating-badge-view__stars'})
        for rate_item in review_rate_items:
            if rate_item.attrs['class'][1] != '_empty':
                review_rate_number += 1

        review_text = item.find('div', {'class': 'business-review-view__body-text _collapsed'}).text

        review = {'index': i, 'reviewer_name': reviewer_name, 'review_rate': review_rate_number,
                  'review_text': review_text}
        reviews.append(review)

    return reviews

