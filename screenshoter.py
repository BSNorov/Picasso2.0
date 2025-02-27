from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from PIL import Image
import os


def take_screenshot(domain, screenshot_dir='screenshots'):
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    screenshot_path = f"{screenshot_dir}/{domain.replace('/', '_')}.png"
    try:
        driver.get(f'https://{domain}')
        success = driver.save_screenshot(screenshot_path)
    except Exception as e:
        print(f'Произошла ошибка при создании скриншота: {e}')
        success = False
    finally:
        driver.quit()
    return success, screenshot_path


def crop_screenshot(path):
    try:
        with Image.open(path) as img:
            print('Текущие размеры изображения:', img.size)
            x = int(input('Введите координату x для начало обрезки: '))
            y = int(input('Введите координату y для начало обрезки: '))
            w = int(input('Введите ширину обрезки: '))
            h = int(input('Введите высоту обрезки: '))
            cropped_image = img.crop((x, y, x + w, y + h))
            cropped_image.save(path)
            print('Изображение обрезано и сохранено')
    except Exception as e:
        print(f'Произошла ошибка при обрезке изображения: {e}')


def main():
    SCREENSHOTS_DIR = 'screenshots'


    if not os.path.exists(SCREENSHOTS_DIR):
        os.makedirs(SCREENSHOTS_DIR)

    while True:
        domain = input("Введите домен сайта (или 'exit' для выхода): ")
        if domain.lower() == 'exit':
            break

        success, screenshot_path = take_screenshot(domain, SCREENSHOTS_DIR)
        if success:
            print(f'Скриншот успешно сохранен: {screenshot_path}')
            if input('Хотите обрезать скришот? (да/нет): ').lower() == 'да':
                crop_screenshot(screenshot_path)
        else:
            print('Не удалось сохранить скриншот')

if __name__ == '__main__':
    main()
