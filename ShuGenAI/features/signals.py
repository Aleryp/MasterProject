from django.db.models.signals import post_migrate
from django.dispatch import receiver
from features.models import Feature, Plans

@receiver(post_migrate)
def create_features_and_plans(sender, **kwargs):
    # Ensure this runs only for your app
    if sender.name != "features":
        return
    # Step 1: Create features
    pro_functions = []
    advanced_functions = []

    black_and_white, _ = Feature.objects.get_or_create(key="black_and_white")
    advanced_functions.append(black_and_white)
    pdf_to_docx, _ = Feature.objects.get_or_create(key="pdf_to_docx")
    advanced_functions.append(pdf_to_docx)
    round_image, _ = Feature.objects.get_or_create(key="round_image")
    advanced_functions.append(round_image)
    pixelate_image, _ = Feature.objects.get_or_create(key="pixelate_image")
    advanced_functions.append(pixelate_image)
    blur_image, _ = Feature.objects.get_or_create(key="blur_image")
    advanced_functions.append(blur_image)
    compress_image, _ = Feature.objects.get_or_create(key="compress_image")
    advanced_functions.append(compress_image)
    heif_to_jpg, _ = Feature.objects.get_or_create(key="heif_to_jpg")
    advanced_functions.append(heif_to_jpg)
    png_to_jpg, _ = Feature.objects.get_or_create(key="png_to_jpg")
    advanced_functions.append(png_to_jpg)
    raw_to_jpg, _ = Feature.objects.get_or_create(key="raw_to_jpg")
    advanced_functions.append(raw_to_jpg)
    tiff_to_jpg, _ = Feature.objects.get_or_create(key="tiff_to_jpg")
    advanced_functions.append(tiff_to_jpg)
    xml_to_json, _ = Feature.objects.get_or_create(key="xml_to_json")
    advanced_functions.append(xml_to_json)
    json_to_xml, _ = Feature.objects.get_or_create(key="json_to_xml")
    advanced_functions.append(json_to_xml)
    xml_to_csv, _ = Feature.objects.get_or_create(key="xml_to_csv")
    advanced_functions.append(xml_to_csv)
    json_to_csv, _ = Feature.objects.get_or_create(key="json_to_csv")
    advanced_functions.append(json_to_csv)
    xls_to_csv, _ = Feature.objects.get_or_create(key="xls_to_csv")
    advanced_functions.append(xls_to_csv)
    xls_to_json, _ = Feature.objects.get_or_create(key="xls_to_json")
    advanced_functions.append(xls_to_json)
    xls_to_xml, _ = Feature.objects.get_or_create(key="xls_to_xml")
    advanced_functions.append(xls_to_xml)
    docx_to_pdf, _ = Feature.objects.get_or_create(key="docx_to_pdf")
    advanced_functions.append(docx_to_pdf)
    compress_pdf, _ = Feature.objects.get_or_create(key="compress_pdf")
    advanced_functions.append(compress_pdf)
    mp4_to_gif, _ = Feature.objects.get_or_create(key="mp4_to_gif")
    advanced_functions.append(mp4_to_gif)
    mkv_to_mp4, _ = Feature.objects.get_or_create(key="mkv_to_mp4")
    advanced_functions.append(mkv_to_mp4)
    mp4_to_mp3, _ = Feature.objects.get_or_create(key="mp4_to_mp3")
    advanced_functions.append(mp4_to_mp3)
    compress_mp4, _ = Feature.objects.get_or_create(key="compress_mp4")
    advanced_functions.append(compress_mp4)
    generate_summary, _ = Feature.objects.get_or_create(key="generate_summary")
    pro_functions.append(generate_summary)
    rewrite_text, _ = Feature.objects.get_or_create(key="rewrite_text")
    pro_functions.append(generate_summary)
    essay_writer, _ = Feature.objects.get_or_create(key="essay_writer")
    pro_functions.append(essay_writer)
    paragraph_writer, _ = Feature.objects.get_or_create(key="paragraph_writer")
    pro_functions.append(paragraph_writer)
    grammar_checker, _ = Feature.objects.get_or_create(key="grammar_checker")
    pro_functions.append(grammar_checker)
    post_writer, _ = Feature.objects.get_or_create(key="post_writer")
    pro_functions.append(post_writer)
    document_code, _ = Feature.objects.get_or_create(key="document_code")
    pro_functions.append(document_code)
    pro_functions = pro_functions + advanced_functions

    # Step 2: Create plans and assign features
    trial_plan, _ = Plans.objects.get_or_create(key="trial")
    trial_plan.features.set(pro_functions)

    advanced_plan, _ = Plans.objects.get_or_create(key="advanced")
    advanced_plan.features.set(advanced_functions)

    pro_plan, _ = Plans.objects.get_or_create(key="pro")
    pro_plan.features.set(pro_functions)
