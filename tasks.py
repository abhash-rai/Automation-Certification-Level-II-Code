from robocorp.tasks import task
from robocorp import browser

from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive

import shutil
import os

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    open_robot_order_website()

    orders = get_orders() 

    for order in orders:
        close_annoying_modal()

        fill_the_form(order)
        
        while True:
            if is_form_submission_failed():
                fill_the_form(order)
            else:
                break

        order_number = order['Order number']
        pdf_path = store_receipt_as_pdf(order_number)
        screenshot_path = screenshot_robot(order_number)
        embed_screenshot_to_receipt(screenshot_path, pdf_path)

        order_another()
    
    archive_receipts()

def open_robot_order_website():
    """Navigates to the robot order URL"""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")

def get_orders():
    """Downloads orders file and retunrs it"""
    if not os.path.exists("orders.csv"):
        http = HTTP()
        http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)
    
    tables = Tables()
    data = tables.read_table_from_csv("orders.csv", header=True)
    return data

def close_annoying_modal():
    """Clicks Ok on the initial alert"""
    page = browser.page()
    page.click('.alert-buttons > button:nth-child(1)')

def fill_the_form(order_detail):
    page = browser.page()
    page.select_option("#head", str(order_detail["Head"]))
    page.click(f"#id-body-{order_detail['Body']}")
    page.fill('//*[@class="form-control"][1]', order_detail['Legs'])
    page.fill("#address", order_detail['Address'])
    page.click(f"#order")

def order_another():
    page = browser.page()
    page.click(f"#order-another")

def store_receipt_as_pdf(order_number):
    """Export receipt data to a pdf file"""
    page = browser.page()
    sales_results_html = page.locator("#receipt").inner_html()

    pdf = PDF()
    pdf_filename = f"output/receipts/{order_number}.pdf"
    pdf.html_to_pdf(sales_results_html, pdf_filename)
    return pdf_filename

def screenshot_robot(order_number):
    page = browser.page()
    screenshot_filename = f"output/receipts_screenshots/{order_number}.png"

    robot_preview_element = page.locator("#robot-preview-image")
    robot_preview_element.screenshot(path=screenshot_filename)
    
    return screenshot_filename

def embed_screenshot_to_receipt(screenshot, pdf_file):
    """Embed a screenshot to the end of a PDF file."""
    pdf = PDF()
    
    pdf.add_watermark_image_to_pdf(
        image_path=screenshot,
        source_path=pdf_file,
        output_path=pdf_file,
    )

def is_form_submission_failed():
    """Checks if the element with class .alert-danger is present"""
    page = browser.page()
    alert_element = page.locator('.alert-danger')
    
    if alert_element.count() > 0 and alert_element.is_visible():
        return True
    return False

def archive_receipts():
    shutil.make_archive('output/receipts', 'zip', 'output/receipts')